import type { ReactNode } from "react";

export type CardProps = {
  title?: ReactNode;
  sub?: ReactNode;
  headExtra?: ReactNode;
  flush?: boolean;
  stack?: boolean;
  error?: boolean;
  children: ReactNode;
  className?: string;
};

export function Card({ title, sub, headExtra, flush, stack, error, children, className }: CardProps) {
  const hasHead = title != null;
  return (
    <section className={`card${error ? " card--error" : ""}${className ? ` ${className}` : ""}`}>
      {hasHead ? (
        <div className={`card__head${error ? " card__head--error" : ""}`}>
          <span>{title}</span>
          {sub ? <span className="card__sub">{sub}</span> : null}
          {headExtra}
        </div>
      ) : null}
      <div
        className={`card__body${flush ? " card__body--flush" : ""}${stack ? " card__body--stack" : ""}`}
      >
        {children}
      </div>
    </section>
  );
}
