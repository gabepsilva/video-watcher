import type { ReactNode } from "react";

type Props = {
  title: string;
  sub?: ReactNode;
  actions?: ReactNode;
};

export function PageHead({ title, sub, actions }: Props) {
  return (
    <div className="page__head">
      <div>
        <h1 className="page__title">{title}</h1>
        {sub ? <p className="page__sub">{sub}</p> : null}
      </div>
      {actions ? <div className="page__actions">{actions}</div> : null}
    </div>
  );
}
