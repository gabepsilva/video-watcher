import type { ReactNode } from "react";

/** Inline SVG icon set (stroke, single-color). */

type IconProps = { size?: number; stroke?: number; className?: string };

function Icon({ children, size = 16, stroke = 1.5, className }: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      {children}
    </svg>
  );
}

export const Icons = {
  Eye: (p: IconProps) => (
    <Icon {...p}>
      <path d="M2 12c2.5-4.5 6-7 10-7s7.5 2.5 10 7c-2.5 4.5-6 7-10 7s-7.5-2.5-10-7z" />
      <circle cx="12" cy="12" r="2.5" />
    </Icon>
  ),
  File: (p: IconProps) => (
    <Icon {...p}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
    </Icon>
  ),
  Yt: (p: IconProps) => (
    <Icon {...p}>
      <rect x="2.5" y="6" width="19" height="12" rx="3" />
      <path d="M10.5 9.5v5l4-2.5z" fill="currentColor" stroke="none" />
    </Icon>
  ),
  Mic: (p: IconProps) => (
    <Icon {...p}>
      <rect x="9" y="3" width="6" height="12" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <path d="M12 18v3" />
    </Icon>
  ),
  Activity: (p: IconProps) => (
    <Icon {...p}>
      <path d="M3 12h4l2-6 4 12 2-6h6" />
    </Icon>
  ),
  Stethoscope: (p: IconProps) => (
    <Icon {...p}>
      <path d="M4 4v6a4 4 0 0 0 8 0V4" />
      <path d="M4 4h2M10 4h2" />
      <path d="M8 14v2a4 4 0 0 0 4 4h2a4 4 0 0 0 4-4v-3" />
      <circle cx="18" cy="11" r="2" />
    </Icon>
  ),
  Sun: (p: IconProps) => (
    <Icon {...p}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4" />
    </Icon>
  ),
  Moon: (p: IconProps) => (
    <Icon {...p}>
      <path d="M21 13.5A8.5 8.5 0 1 1 10.5 3 7 7 0 0 0 21 13.5z" />
    </Icon>
  ),
  Cpu: (p: IconProps) => (
    <Icon {...p}>
      <rect x="6" y="6" width="12" height="12" rx="2" />
      <rect x="10" y="10" width="4" height="4" />
      <path d="M2 10h2M2 14h2M20 10h2M20 14h2M10 2v2M14 2v2M10 20v2M14 20v2" />
    </Icon>
  ),
  Box: (p: IconProps) => (
    <Icon {...p}>
      <path d="M21 8.5 12 4 3 8.5l9 4.5 9-4.5z" />
      <path d="M3 8.5V16l9 4.5L21 16V8.5" />
      <path d="M12 13v7.5" />
    </Icon>
  ),
  Python: (p: IconProps) => (
    <Icon {...p}>
      <path d="M9 4h6a2 2 0 0 1 2 2v4H7" />
      <path d="M15 20H9a2 2 0 0 1-2-2v-4h10" />
      <circle cx="10" cy="7" r=".7" fill="currentColor" />
      <circle cx="14" cy="17" r=".7" fill="currentColor" />
    </Icon>
  ),
  Plus: (p: IconProps) => (
    <Icon {...p}>
      <path d="M12 5v14M5 12h14" />
    </Icon>
  ),
  Check: (p: IconProps) => (
    <Icon {...p}>
      <path d="M5 12.5 9.5 17 19 7" />
    </Icon>
  ),
  Chev: (p: IconProps) => (
    <Icon {...p}>
      <path d="M9 6l6 6-6 6" />
    </Icon>
  ),
  Upload: (p: IconProps) => (
    <Icon {...p}>
      <path d="M12 16V4M6 10l6-6 6 6" />
      <path d="M4 18v2h16v-2" />
    </Icon>
  ),
  Download: (p: IconProps) => (
    <Icon {...p}>
      <path d="M12 4v12M6 10l6 6 6-6" />
      <path d="M4 18v2h16v-2" />
    </Icon>
  ),
  Refresh: (p: IconProps) => (
    <Icon {...p}>
      <path d="M4 12a8 8 0 0 1 14-5l2 2" />
      <path d="M20 4v4h-4" />
      <path d="M20 12a8 8 0 0 1-14 5l-2-2" />
      <path d="M4 20v-4h4" />
    </Icon>
  ),
  Stop: (p: IconProps) => (
    <Icon {...p}>
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </Icon>
  ),
  Alert: (p: IconProps) => (
    <Icon {...p}>
      <path d="M12 8v5M12 16h.01" />
      <path d="M10.3 3.7 2.4 18.2a1.5 1.5 0 0 0 1.3 2.2h16.6a1.5 1.5 0 0 0 1.3-2.2L13.7 3.7a1.5 1.5 0 0 0-2.6 0z" />
    </Icon>
  ),
  ArrowLeft: (p: IconProps) => (
    <Icon {...p}>
      <path d="M15 6l-6 6 6 6" />
    </Icon>
  ),
};
