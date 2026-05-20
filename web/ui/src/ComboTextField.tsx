/** Text input with HTML ``datalist`` presets (type freely or pick a suggestion). */

type Props = {
  name: string;
  label: string;
  listId: string;
  options: string[];
  defaultValue?: string;
  placeholder?: string;
};

export function ComboTextField({
  name,
  label,
  listId,
  options,
  defaultValue = "",
  placeholder,
}: Props) {
  return (
    <label>
      {label}
      <input name={name} list={listId} defaultValue={defaultValue} placeholder={placeholder} />
      <datalist id={listId}>
        {options.map((o) => (
          <option key={o} value={o} />
        ))}
      </datalist>
    </label>
  );
}
