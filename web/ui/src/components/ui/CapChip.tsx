type DotStatus = "ok" | "warn" | "err" | "live" | "none";

type Props = {
  label: string;
  value: string;
  status?: DotStatus;
  title?: string;
};

export function CapChip({ label, value, status = "none", title }: Props) {
  const dotClass = status === "none" ? "dot" : `dot dot--${status}`;
  return (
    <div className="cap-chip" title={title}>
      <span className={dotClass} />
      <span className="cap-chip__label">{label}</span>
      <span className="cap-chip__val">{value}</span>
    </div>
  );
}
