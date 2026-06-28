import { useState, useEffect } from "react";

const METRICS = [
  {
    key: "faithfulness",
    label: "Faithfulness",
    description: "Answer grounded in context",
    color: "#6366f1",
  },
  {
    key: "answer_relevancy",
    label: "Relevancy",
    description: "Answer addresses the question",
    color: "#0ea5e9",
  },
  {
    key: "context_precision",
    label: "Precision",
    description: "Retrieved docs are on-topic",
    color: "#10b981",
  },
  {
    key: "context_recall",
    label: "Recall",
    description: "Context covers the answer",
    color: "#f59e0b",
  },
];

function ScoreGauge({ value, color, animated }) {
  const pct = Math.round((value || 0) * 100);
  const dash = 2 * Math.PI * 36;
  const offset = dash - (dash * pct) / 100;

  return (
    <div className="gauge-wrap">
      <svg viewBox="0 0 80 80" width="80" height="80">
        <circle cx="40" cy="40" r="36" fill="none" stroke="var(--gauge-bg)" strokeWidth="7" />
        <circle
          cx="40" cy="40" r="36"
          fill="none"
          stroke={color}
          strokeWidth="7"
          strokeDasharray={dash}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 40 40)"
          style={{ transition: animated ? "stroke-dashoffset 0.8s ease" : "none" }}
        />
        <text x="40" y="45" textAnchor="middle" fontSize="16" fontWeight="700" fill="var(--text-primary)">
          {pct}
        </text>
      </svg>
    </div>
  );
}

function MetricBar({ metric, value }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="metric-bar-row">
      <div className="metric-bar-label">
        <span>{metric.label}</span>
        <span className="metric-pct" style={{ color: metric.color }}>{pct}%</span>
      </div>
      <div className="metric-bar-track">
        <div
          className="metric-bar-fill"
          style={{
            width: `${pct}%`,
            background: metric.color,
            transition: "width 0.6s cubic-bezier(.4,0,.2,1)",
          }}
        />
      </div>
      <p className="metric-desc">{metric.description}</p>
    </div>
  );
}

export default function EvalPanel({ evaluation }) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    if (evaluation) {
      setAnimated(false);
      const t = setTimeout(() => setAnimated(true), 50);
      return () => clearTimeout(t);
    }
  }, [evaluation]);

  const overall = evaluation?.overall_score ?? null;
  const grade =
    overall === null ? "—"
    : overall >= 0.85 ? "A"
    : overall >= 0.70 ? "B"
    : overall >= 0.55 ? "C"
    : "D";

  const gradeColor =
    overall === null ? "var(--text-muted)"
    : overall >= 0.85 ? "#10b981"
    : overall >= 0.70 ? "#f59e0b"
    : "#ef4444";

  return (
    <div className="eval-panel">
      <div className="eval-panel-header">
        <h3>Response Quality</h3>
        <span className="eval-framework">RAGAS</span>
      </div>

      {/* Overall score */}
      <div className="overall-score-card">
        <div className="overall-gauge">
          <ScoreGauge value={overall ?? 0} color={gradeColor} animated={animated} />
        </div>
        <div className="overall-info">
          <div className="overall-grade" style={{ color: gradeColor }}>{grade}</div>
          <div className="overall-label">Overall</div>
          {evaluation && (
            <div className="overall-pct">{Math.round((overall ?? 0) * 100)}%</div>
          )}
        </div>
      </div>

      {/* Individual metrics */}
      <div className="metrics-list">
        {METRICS.map((m) => (
          <MetricBar
            key={m.key}
            metric={m}
            value={evaluation?.[m.key] ?? 0}
          />
        ))}
      </div>

      {/* Performance stats */}
      {evaluation && (
        <div className="perf-stats">
          <div className="perf-stat">
            <span className="perf-icon">⏱</span>
            <div>
              <div className="perf-value">{evaluation.latency_ms.toFixed(0)}ms</div>
              <div className="perf-label">Latency</div>
            </div>
          </div>
          <div className="perf-stat">
            <span className="perf-icon">🔤</span>
            <div>
              <div className="perf-value">{evaluation.tokens_used.toLocaleString()}</div>
              <div className="perf-label">Tokens</div>
            </div>
          </div>
        </div>
      )}

      {!evaluation && (
        <div className="eval-empty">
          <p>Metrics appear after each response.</p>
          <p className="eval-empty-sub">RAGAS evaluates faithfulness, relevancy, precision, and recall in real-time.</p>
        </div>
      )}
    </div>
  );
}
