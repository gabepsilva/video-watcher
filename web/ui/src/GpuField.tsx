import { useEffect, useState } from "react";
import type { ApiMeta } from "./api";

type Props = {
  meta: ApiMeta | null;
  /** For uncontrolled forms: hidden input name. Omit for controlled mic UI. */
  name?: string;
  checked?: boolean;
  onChange?: (checked: boolean) => void;
};

export function GpuField({ meta, name = "gpu", checked, onChange }: Props) {
  const pending = meta === null;
  const available = meta?.gpu_available === true;
  const [internal, setInternal] = useState(false);

  useEffect(() => {
    if (checked === undefined) {
      setInternal(available);
    }
  }, [available, checked]);

  const isChecked = checked !== undefined ? checked && available : internal;
  const disabled = pending || !available;

  function toggle(next: boolean) {
    if (disabled) {
      return;
    }
    if (onChange) {
      onChange(next);
    } else {
      setInternal(next);
    }
  }

  return (
    <label
      className={`check-inline${disabled ? " muted" : ""}`}
      title={
        disabled
          ? "No GPU for jobs (native CUDA/ROCm or Docker with host GPU required)"
          : undefined
      }
    >
      <input
        name={onChange ? undefined : name}
        type="checkbox"
        checked={isChecked}
        disabled={disabled}
        onChange={(e) => toggle(e.target.checked)}
      />
      GPU{pending ? " (checking…)" : disabled ? " (unavailable)" : ""}
    </label>
  );
}
