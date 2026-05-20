import type { ApiMeta } from "./api";
import { ComboTextField } from "./ComboTextField";
import { GpuField } from "./GpuField";

type Props = {
  meta: ApiMeta | null;
  languageListId: string;
  formatsListId: string;
  languagePlaceholder?: string;
};

export function JobFormOptions({
  meta,
  languageListId,
  formatsListId,
  languagePlaceholder = "e.g. en (optional)",
}: Props) {
  const languages = meta?.popular_languages ?? ["en", "es", "fr", "de", "pt"];
  const formatPresets = meta?.format_presets ?? ["all", "srt", "vtt", "txt", "srt,vtt,txt"];

  return (
    <>
      <ComboTextField
        name="language"
        label="Language (optional ISO code)"
        listId={languageListId}
        options={languages}
        placeholder={languagePlaceholder}
      />
      <ComboTextField
        name="formats"
        label="Formats"
        listId={formatsListId}
        options={formatPresets}
        defaultValue="all"
        placeholder="all or srt,vtt,txt"
      />
      <div className="checks">
        <GpuField meta={meta} />
      </div>
    </>
  );
}
