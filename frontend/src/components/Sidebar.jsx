export default function Sidebar({ conversations, activeId, onSelect, onNewChat, onUpload }) {
  return (
    <nav className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-brand">
          <span className="brand-icon">⬡</span>
          <span className="brand-name">RAG Chat</span>
        </div>

        <button className="btn-new-chat" onClick={onNewChat}>
          <span>+</span> New chat
        </button>

        <button className="btn-upload" onClick={onUpload}>
          <span>↑</span> Upload docs
        </button>
      </div>

      <div className="sidebar-convos">
        <div className="convos-label">Conversations</div>
        {conversations.length === 0 && (
          <div className="convos-empty">No conversations yet</div>
        )}
        {conversations.map((conv) => (
          <button
            key={conv.id}
            className={`conv-item ${conv.id === activeId ? "active" : ""}`}
            onClick={() => onSelect(conv.id)}
          >
            <span className="conv-icon">💬</span>
            <span className="conv-title">{conv.title || "New conversation"}</span>
          </button>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="stack-badge">
          <span>FastAPI · ChromaDB · GPT-4o</span>
        </div>
      </div>
    </nav>
  );
}
