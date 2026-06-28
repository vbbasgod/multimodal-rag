import { useState } from "react";
import EvalBadge from "./EvalBadge";

export default function MessageBubble({ message }) {
  const [showContexts, setShowContexts] = useState(false);
  const isUser = message.role === "user";

  return (
    <div className={`message-wrapper ${isUser ? "user" : "assistant"}`}>
      <div className="avatar">{isUser ? "U" : "⬡"}</div>

      <div className="bubble-group">
        {/* Image preview for user uploads */}
        {message.image && (
          <div className="image-preview-wrap">
            <img src={message.image} alt="Upload" className="msg-image" />
          </div>
        )}

        <div className={`bubble ${isUser ? "bubble-user" : "bubble-assistant"} ${message.isError ? "bubble-error" : ""}`}>
          {message.loading ? (
            <div className="typing-dots">
              <span /><span /><span />
            </div>
          ) : (
            <div className="bubble-text">{message.content}</div>
          )}
        </div>

        {/* Evaluation badge below assistant messages */}
        {!isUser && !message.loading && message.evaluation && (
          <div className="eval-row">
            <EvalBadge score={message.evaluation.overall_score} />
            <span className="eval-meta">
              {message.evaluation.latency_ms.toFixed(0)}ms · {message.evaluation.tokens_used} tokens
            </span>
            {message.contexts?.length > 0 && (
              <button
                className="ctx-toggle"
                onClick={() => setShowContexts((p) => !p)}
              >
                {showContexts ? "Hide" : "Show"} {message.contexts.length} sources
              </button>
            )}
          </div>
        )}

        {/* Retrieved contexts */}
        {showContexts && message.contexts && (
          <div className="contexts-list">
            {message.contexts.map((ctx, i) => (
              <div key={ctx.document_id} className="ctx-item">
                <div className="ctx-header">
                  <span className={`modality-badge ${ctx.modality}`}>{ctx.modality}</span>
                  <span className="ctx-score">{(ctx.score * 100).toFixed(1)}% match</span>
                  {ctx.metadata?.source && (
                    <span className="ctx-source">{ctx.metadata.source}</span>
                  )}
                </div>
                <p className="ctx-content">{ctx.content.slice(0, 300)}{ctx.content.length > 300 ? "…" : ""}</p>
              </div>
            ))}
          </div>
        )}

        <span className="msg-time">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}
