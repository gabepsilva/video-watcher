import { Button } from "./Button";

type Props = {
  value: string[];
  onChange: (v: string[]) => void;
  options: string[];
};

export function FormatChips({ value, onChange, options }: Props) {
  const toggle = (f: string) => {
    if (value.includes(f)) {
      onChange(value.filter((x) => x !== f));
    } else {
      onChange([...value, f]);
    }
  };

  return (
    <div className="u-flex u-gap-2" style={{ flexWrap: "wrap" }}>
      {options.map((f) => (
        <Button
          key={f}
          type="button"
          variant={value.includes(f) ? "chip-on" : "chip"}
          size="sm"
          onClick={() => toggle(f)}
        >
          {f}
        </Button>
      ))}
    </div>
  );
}
