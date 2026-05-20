type JobState = string;

const KNOWN = new Set(["running", "succeeded", "failed", "queued", "canceled"]);

export function StateBadge({ state }: { state: JobState }) {
  const mod = KNOWN.has(state) ? state : "queued";
  return (
    <span className={`state-badge state-badge--${mod}`}>
      <span className="dot" />
      {state}
    </span>
  );
}
