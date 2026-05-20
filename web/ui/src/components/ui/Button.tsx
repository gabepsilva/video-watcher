import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "default" | "primary" | "ghost" | "chip" | "chip-on";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: "default" | "sm";
  children: ReactNode;
};

function btnClass(variant: Variant, size: string, className?: string) {
  const parts = ["btn"];
  if (variant === "primary") parts.push("btn--primary");
  if (variant === "ghost") parts.push("btn--ghost");
  if (variant === "chip") parts.push("btn--chip");
  if (variant === "chip-on") parts.push("btn--chip-on");
  if (size === "sm") parts.push("btn--sm");
  if (className) parts.push(className);
  return parts.join(" ");
}

export function Button({ variant = "default", size = "default", className, children, ...rest }: Props) {
  return (
    <button type="button" className={btnClass(variant, size, className)} {...rest}>
      {children}
    </button>
  );
}
