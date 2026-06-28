import { useState, useRef, useEffect, useCallback } from "react";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import { sendMessage } from "../services/api";
import { useChatStore } from "../hooks/useChatStore";

export default function ChatWindow({ conversationId, onEvalUpdate }) {
  const { getMessages, addMessage, updateMessage } = useChatStore();
  const messages = getMessages(conversationId);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(
    async (text, imageFile) => {
      if (!text.trim() && !imageFile) return;
      setError(null);

      // Optimistic user message
      const userMsg = {
        id: Date.now().toString(),
        role: "user",
        content: text,
        image: imageFile ? URL.createObjectURL(imageFile) : null,
        timestamp: new Date().toISOString(),
      };
      addMessage(conversationId, userMsg);
      setLoading(true);

      // Placeholder assistant message
      const assistantId = (Date.now() + 1).toString();
      addMessage(conversationId, {
        id: assistantId,
        role: "assistant",
        content: "",
        loading: true,
        timestamp: new Date().toISOString(),
      });

      try {
        // Build history for context
        const history = messages.slice(-10).map((m) => ({
          role: m.role,
          content: m.content,
        }));

        // Convert image to base64 if present
        let imageBase64 = null;
        if (imageFile) {
          imageBase64 = await fileToBase64(imageFile);
        }

        const response = await sendMessage({
          message: text,
          conversation_id: conversationId,
          history,
          image_base64: imageBase64,
          use_rag: true,
          top_k: 5,
        });

        updateMessage(conversationId, assistantId, {
          content: response.response,
          loading: false,
          evaluation: response.evaluation,
          contexts: response.retrieved_contexts,
          model: response.model_used,
        });

        onEvalUpdate?.(response.evaluation);
      } catch (err) {
        setError(err.message || "Something went wrong");
        updateMessage(conversationId, assistantId, {
          content: "Sorry, I encountered an error. Please try again.",
          loading: false,
          isError: true,
        });
      } finally {
        setLoading(false);
      }
    },
    [conversationId, messages, addMessage, updateMessage, onEvalUpdate]
  );

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div className="chat-header-info">
          <span className="chat-logo">⬡</span>
          <div>
            <h2>Multimodal RAG</h2>
            <span className="chat-subtitle">GPT-4o · ChromaDB · RAGAS</span>
          </div>
        </div>
        <div className="status-dot active" title="Connected" />
      </div>

      <div className="messages-area">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">⬡</div>
            <h3>Ask anything</h3>
            <p>Upload documents, images, or PDFs — then ask questions about them.</p>
            <div className="example-chips">
              {["Summarize the uploaded document", "What does the chart show?", "Compare the data in section 2"].map(
                (ex) => (
                  <button key={ex} className="chip" onClick={() => handleSend(ex, null)}>
                    {ex}
                  </button>
                )
              )}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {error && (
          <div className="error-toast">
            <span>⚠</span> {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={handleSend} loading={loading} />
    </div>
  );
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
