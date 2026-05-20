import type { ReactNode } from "react";
import { Icons } from "../../icons/Icons";

type Props = {
  topbar: ReactNode;
  sidebar: ReactNode;
  children: ReactNode;
};

export function ConsoleShell({ topbar, sidebar, children }: Props) {
  return (
    <div className="console">
      <div className="console__brand">
        <div className="console__brand-mark" aria-hidden>
          <Icons.Eye size={13} stroke={2} />
        </div>
        <div className="console__brand-name">
          video-watcher <span className="u-muted">/ console</span>
        </div>
      </div>
      {topbar}
      {sidebar}
      <main className="console__main">{children}</main>
    </div>
  );
}
