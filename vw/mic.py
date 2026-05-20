"""Microphone transcription: VAD phrase detection, transcribe on pause."""

from __future__ import annotations

import contextlib
import io
import queue
import sys
import threading
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import whisper
from whisper.audio import SAMPLE_RATE

from vw.transcribe import _status, load_whisper_model

# 30 ms frames — good balance for pause detection.
_FRAME_MS = 30
# End a phrase after this much trailing silence.
_SILENCE_END_S = 0.6
# Ignore very short blips ( cough, clicks ).
_MIN_PHRASE_S = 0.25
# Force a phrase break on long monologues.
_MAX_PHRASE_S = 30.0
# Skip near-silent audio before calling Whisper.
_SILENCE_PEAK = 0.001
# Initial speech threshold; adapts to ambient noise.
_SPEECH_RMS_FLOOR = 0.008

_TRANSCRIBE_SENTINEL = object()


def _input_sample_rate(sd) -> int:
    try:
        info = sd.query_devices(kind="input")
        return int(info["default_samplerate"])
    except Exception:
        return SAMPLE_RATE


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    if orig_sr == target_sr or len(audio) == 0:
        return audio.astype(np.float32, copy=False)
    duration = len(audio) / orig_sr
    target_len = int(round(duration * target_sr))
    if target_len <= 0:
        return np.array([], dtype=np.float32)
    x_old = np.linspace(0.0, duration, num=len(audio), endpoint=False)
    x_new = np.linspace(0.0, duration, num=target_len, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def _block_rms(block: np.ndarray) -> float:
    if block.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(block, dtype=np.float64))))


class _PhraseBuffer:
    """Accumulate mic blocks until VAD sees a pause (or max phrase length)."""

    def __init__(self, input_sr: int) -> None:
        self.input_sr = input_sr
        self._blocks: list[np.ndarray] = []
        self._trailing_silence_ms = 0
        self._in_phrase = False
        self._noise_rms = _SPEECH_RMS_FLOOR

    def _speech_threshold(self) -> float:
        return max(_SPEECH_RMS_FLOOR, self._noise_rms * 3.0)

    def _phrase_seconds(self) -> float:
        samples = sum(len(b) for b in self._blocks)
        return samples / self.input_sr

    def feed(self, block: np.ndarray) -> bool:
        """Append one block; return True when the phrase should be transcribed."""
        rms = _block_rms(block)
        threshold = self._speech_threshold()
        is_speech = rms >= threshold

        if is_speech:
            self._in_phrase = True
            self._blocks.append(block)
            self._trailing_silence_ms = 0
        elif self._in_phrase:
            self._blocks.append(block)
            self._trailing_silence_ms += _FRAME_MS
        else:
            self._noise_rms = 0.95 * self._noise_rms + 0.05 * rms

        if not self._in_phrase:
            return False

        phrase_s = self._phrase_seconds()
        if phrase_s >= _MAX_PHRASE_S:
            return True
        if (
            self._trailing_silence_ms >= int(_SILENCE_END_S * 1000)
            and phrase_s >= _MIN_PHRASE_S
        ):
            return True
        return False

    def take_audio(self) -> np.ndarray:
        if not self._blocks:
            return np.array([], dtype=np.float32)
        audio = np.concatenate(self._blocks).astype(np.float32, copy=False)
        self._blocks.clear()
        self._trailing_silence_ms = 0
        self._in_phrase = False
        return audio

    @property
    def has_audio(self) -> bool:
        return bool(self._blocks) and self._phrase_seconds() >= _MIN_PHRASE_S


def _transcribe_phrase(model, audio: np.ndarray, transcribe_kwargs: dict) -> str | None:
    if len(audio) < int(_MIN_PHRASE_S * SAMPLE_RATE):
        return None
    if float(np.abs(audio).max()) < _SILENCE_PEAK:
        return None

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
        warnings.filterwarnings(
            "ignore", message="Performing inference on CPU when CUDA is available"
        )
        with contextlib.redirect_stderr(io.StringIO()):
            result = whisper.transcribe(model, audio, **transcribe_kwargs)

    text = result.get("text", "").strip()
    return text or None


def _emit_phrase(
    text: str,
    *,
    outfile,
    emit_lock: threading.Lock,
) -> None:
    with emit_lock:
        print(text, flush=True)
        if outfile is not None:
            outfile.write(text + "\n")
            outfile.flush()


def _capture_loop(
    *,
    sd,
    block_frames: int,
    input_sr: int,
    block_queue: queue.Queue,
    stop_event: threading.Event,
) -> None:
    while not stop_event.is_set():
        block = sd.rec(
            block_frames,
            samplerate=input_sr,
            channels=1,
            dtype=np.float32,
        )
        sd.wait()
        if stop_event.is_set():
            break
        block_queue.put(block)


def _transcribe_loop(
    *,
    model,
    transcribe_kwargs: dict,
    transcribe_queue: queue.Queue,
    outfile,
    emit_lock: threading.Lock,
) -> None:
    while True:
        item = transcribe_queue.get()
        if item is _TRANSCRIBE_SENTINEL:
            transcribe_queue.task_done()
            break
        assert isinstance(item, np.ndarray)
        text = _transcribe_phrase(model, item, transcribe_kwargs)
        if text:
            _emit_phrase(text, outfile=outfile, emit_lock=emit_lock)
        transcribe_queue.task_done()


def listen_microphone(
    *,
    model_name: str,
    device: str,
    language: str | None,
    output_path: Path | None,
) -> None:
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise ImportError(
            "Microphone mode requires sounddevice. Install with:\n"
            f"  {sys.executable} -m pip install sounddevice"
        ) from exc

    input_sr = _input_sample_rate(sd)
    _status(
        f"Microphone mode — transcribe on pause (~{_SILENCE_END_S:g}s silence), "
        f"capture never blocks on Whisper ({input_sr} Hz → {SAMPLE_RATE} Hz, Ctrl+C to stop)"
    )
    if model_name not in ("turbo", "small", "medium", "large"):
        _status("Tip: use -m turbo --gpu for best microphone accuracy.")
    try:
        device_name = sd.query_devices(kind="input")["name"]
        _status(f"Input device: {device_name}")
    except Exception:
        pass

    model = load_whisper_model(model_name, device)

    transcribe_kwargs: dict = {
        "temperature": 0,
        "verbose": False,
        "condition_on_previous_text": False,
    }
    if language:
        transcribe_kwargs["language"] = language

    block_frames = max(1, int(input_sr * _FRAME_MS / 1000))
    phrase_buf = _PhraseBuffer(input_sr)

    outfile = None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        outfile = output_path.open("a", encoding="utf-8")
        _status(f"Appending transcript to {output_path}")

    emit_lock = threading.Lock()
    block_queue: queue.Queue = queue.Queue()
    transcribe_queue: queue.Queue = queue.Queue()
    stop_event = threading.Event()

    transcribe_thread = threading.Thread(
        target=_transcribe_loop,
        kwargs={
            "model": model,
            "transcribe_kwargs": transcribe_kwargs,
            "transcribe_queue": transcribe_queue,
            "outfile": outfile,
            "emit_lock": emit_lock,
        },
        name="vw-mic-transcribe",
        daemon=True,
    )
    transcribe_thread.start()

    capture_thread = threading.Thread(
        target=_capture_loop,
        kwargs={
            "sd": sd,
            "block_frames": block_frames,
            "input_sr": input_sr,
            "block_queue": block_queue,
            "stop_event": stop_event,
        },
        name="vw-mic-capture",
        daemon=True,
    )
    capture_thread.start()

    def enqueue_phrase(*, force: bool = False) -> None:
        if force and not phrase_buf.has_audio:
            return
        raw = phrase_buf.take_audio()
        if raw.size == 0:
            return
        audio = _resample(raw, input_sr)
        if audio.size == 0:
            return
        transcribe_queue.put(audio)

    print("Listening… (pause briefly after each phrase)", file=sys.stderr, flush=True)

    try:
        while True:
            try:
                block = block_queue.get(timeout=0.25)
            except queue.Empty:
                continue
            flat = block.flatten()
            if phrase_buf.feed(flat):
                enqueue_phrase()
    except KeyboardInterrupt:
        _status("\nStopped.")
    finally:
        stop_event.set()
        capture_thread.join(timeout=3.0)

        while True:
            try:
                block = block_queue.get_nowait()
            except queue.Empty:
                break
            if phrase_buf.feed(block.flatten()):
                enqueue_phrase()

        enqueue_phrase(force=True)
        transcribe_queue.put(_TRANSCRIBE_SENTINEL)
        transcribe_thread.join()

        if outfile is not None:
            outfile.close()


def default_mic_output_path(output_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return output_dir / f"mic-{stamp}.txt"
