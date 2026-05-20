import { Icons } from "../../icons/Icons";

export type Route =
  | "new"
  | "mic"
  | "jobs"
  | "diag"
  | { job: string };

type Props = {
  route: Route;
  onRoute: (r: Route) => void;
  activeJobCount: number;
  runningCount: number;
};

function routeKey(route: Route): string {
  if (typeof route === "object") return "jobs";
  return route;
}

function NavItem({
  icon: Ico,
  label,
  kbd,
  count,
  countLive,
  active,
  onClick,
}: {
  icon: typeof Icons.File;
  label: string;
  kbd?: string;
  count?: number | null;
  countLive?: boolean;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button type="button" className={`nav__item${active ? " nav__item--active" : ""}`} onClick={onClick}>
      <span className="nav__icon">
        <Ico size={15} stroke={1.6} />
      </span>
      <span>{label}</span>
      {count != null && count > 0 ? (
        <span className={`nav__count${countLive ? " nav__count--live" : ""}`}>
          {countLive ? <span className="dot dot--live" style={{ width: 5, height: 5, boxShadow: "none" }} /> : null}
          {count}
        </span>
      ) : null}
      {kbd && (count == null || count === 0) ? <span className="nav__kbd">{kbd}</span> : null}
    </button>
  );
}

export function Sidebar({ route, onRoute, activeJobCount, runningCount }: Props) {
  const key = routeKey(route);
  const onJob = typeof route === "object";

  return (
    <aside className="sidebar console__sidebar">
      <div className="nav__label">Capture</div>
      <NavItem
        icon={Icons.Plus}
        label="New transcription"
        kbd="N"
        active={key === "new"}
        onClick={() => onRoute("new")}
      />
      <NavItem icon={Icons.Mic} label="Microphone" kbd="M" active={key === "mic"} onClick={() => onRoute("mic")} />

      <div className="nav__label">Activity</div>
      <NavItem
        icon={Icons.Activity}
        label="Jobs"
        count={activeJobCount > 0 ? activeJobCount : null}
        countLive={runningCount > 0}
        active={key === "jobs" || onJob}
        onClick={() => onRoute("jobs")}
      />

      <div className="nav__label">System</div>
      <NavItem
        icon={Icons.Stethoscope}
        label="Diagnostics"
        active={key === "diag"}
        onClick={() => onRoute("diag")}
      />

      <div className="sidebar__foot">
        <div className="sidebar__foot-row">
          <span>vw</span>
          <span>web</span>
        </div>
        <div className="sidebar__foot-row">
          <span>proxy</span>
          <span>/api → 8765</span>
        </div>
      </div>
    </aside>
  );
}
