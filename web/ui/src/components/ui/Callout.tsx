import type { ReactNode } from "react";
import { Icons } from "../../icons/Icons";

type Variant = "warn" | "info" | "err";

type Props = {
  variant?: Variant;
  title: string;
  children: ReactNode;
};

export function Callout({ variant = "warn", title, children }: Props) {
  const mod = variant === "warn" ? "" : ` callout--${variant}`;
  return (
    <div className={`callout${mod}`}>
      <Icons.Alert size={16} className="callout__ico" />
      <div>
        <div className="callout__title">{title}</div>
        <div className="callout__body">{children}</div>
      </div>
    </div>
  );
}
