export default function EvalBadge({ score }) {
  const pct = Math.round((score || 0) * 100);
  const color =
    pct >= 85 ? "#10b981"
    : pct >= 70 ? "#f59e0b"
    : pct >= 50 ? "#f97316"
    : "#ef4444";

  const label =
    pct >= 85 ? "Excellent"
    : pct >= 70 ? "Good"
    : pct >= 50 ? "Fair"
    : "Poor";

  return (
    <span className="eval-badge" style={{ borderColor: color, color }}>
      <svg width="10" height="10" viewBox="0 0 10 10" style={{ marginRight: 4 }}>
        <circle cx="5" cy="5" r="4" fill="none" stroke={color} strokeWidth="1.5" />
        <circle
          cx="5" cy="5" r="4"
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeDasharray={`${2 * Math.PI * 4}`}
          strokeDashoffset={`${2 * Math.PI * 4 * (1 - pct / 100)}`}
          transform="rotate(-90 5 5)"
          opacity="0.8"
        />
      </svg>
      {pct}% · {label}
    </span>
  );
}
