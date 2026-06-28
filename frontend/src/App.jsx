import { useState, useCallback } from "react";
import ChatWindow from "./components/ChatWindow";
import Sidebar from "./components/Sidebar";
import EvalPanel from "./components/EvalPanel";
import UploadModal from "./components/UploadModal";
import { useChatStore } from "./hooks/useChatStore";
import "./App.css";

export default function App() {
  const { conversations, activeId, setActiveId, createConversation } = useChatStore();
  const [showUpload, setShowUpload] = useState(false);
  const [lastEval, setLastEval] = useState(null);
  const [evalPanelOpen, setEvalPanelOpen] = useState(true);

  const handleNewChat = useCallback(() => {
    createConversation();
  }, [createConversation]);

  return (
    <div className="app-shell">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onNewChat={handleNewChat}
        onUpload={() => setShowUpload(true)}
      />

      <main className="chat-main">
        <ChatWindow
          conversationId={activeId}
          onEvalUpdate={setLastEval}
        />
      </main>

      <aside className={`eval-aside ${evalPanelOpen ? "open" : "collapsed"}`}>
        <button
          className="eval-toggle"
          onClick={() => setEvalPanelOpen((p) => !p)}
          title={evalPanelOpen ? "Hide metrics" : "Show metrics"}
        >
          {evalPanelOpen ? "›" : "‹"}
        </button>
        {evalPanelOpen && <EvalPanel evaluation={lastEval} />}
      </aside>

      {showUpload && <UploadModal onClose={() => setShowUpload(false)} />}
    </div>
  );
}
