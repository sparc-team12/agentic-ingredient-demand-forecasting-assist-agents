// Small reusable component (ACRI-61): renders a visible, textual (not
// color-only) flag when `when` is `true`; renders nothing otherwise.
// Reused for both AC3 ("no supplier mapped") and AC5 ("safety margin not
// set") — a single, directly-testable source of truth for the gap-flag
// copy/treatment, per the implementation plan's Q3 resolution (plain,
// accessible text, no color-only indicator).
interface GapFlagProps {
  when: boolean;
  text: string;
}

export function GapFlag({ when, text }: GapFlagProps) {
  if (!when) {
    return null;
  }
  return (
    <span role="alert" className="badge badge--warning">
      {text}
    </span>
  );
}
