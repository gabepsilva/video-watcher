import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

type LabelProps = {
  label: ReactNode;
  hint?: ReactNode;
  htmlFor?: string;
};

export function FieldLabel({ label, hint, htmlFor }: LabelProps) {
  return (
    <label className="field__label" htmlFor={htmlFor}>
      <span>{label}</span>
      {hint ? <span className="field__hint">{hint}</span> : null}
    </label>
  );
}

export function Field({ children }: { children: ReactNode }) {
  return <div className="field">{children}</div>;
}

export function FieldRow({ children, three }: { children: ReactNode; three?: boolean }) {
  return <div className={`field-row${three ? " field-row--three" : ""}`}>{children}</div>;
}

export function TextInput({
  mono,
  className,
  ...rest
}: InputHTMLAttributes<HTMLInputElement> & { mono?: boolean }) {
  return (
    <input
      className={`input${mono ? " input--mono" : ""}${className ? ` ${className}` : ""}`}
      {...rest}
    />
  );
}

export function SelectInput({ className, children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={`select${className ? ` ${className}` : ""}`} {...rest}>
      {children}
    </select>
  );
}

export function FieldHelp({ children, warn, err }: { children: ReactNode; warn?: boolean; err?: boolean }) {
  const mod = err ? " field__help--err" : warn ? " field__help--warn" : "";
  return <div className={`field__help${mod}`}>{children}</div>;
}

export function CheckboxRow({
  checked,
  disabled,
  onChange,
  label,
  sub,
  name,
}: {
  checked: boolean;
  disabled?: boolean;
  onChange: (v: boolean) => void;
  label: ReactNode;
  sub?: ReactNode;
  name?: string;
}) {
  return (
    <label className="checkbox-row">
      <input
        name={name}
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span>
        <div className="checkbox-row__lbl">{label}</div>
        {sub ? <div className="checkbox-row__sub">{sub}</div> : null}
      </span>
    </label>
  );
}
