import { useState, useRef } from "react";

export default function ChatInput({ onSend, loading }) {
  const [text, setText] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const fileRef = useRef();

  const handleSubmit = () => {
    if (loading || (!text.trim() && !imageFile)) return;
    onSend(text.trim(), imageFile);
    setText("");
    setImageFile(null);
    setImagePreview(null);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  return (
    <div className="chat-input-area">
      {imagePreview && (
        <div className="input-image-preview">
          <img src={imagePreview} alt="Attached" />
          <button
            className="remove-image"
            onClick={() => { setImageFile(null); setImagePreview(null); }}
          >×</button>
        </div>
      )}

      <div className="input-row">
        <button
          className="attach-btn"
          onClick={() => fileRef.current?.click()}
          title="Attach image"
          disabled={loading}
        >
          📎
        </button>

        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          style={{ display: "none" }}
          onChange={handleFile}
        />

        <textarea
          className="chat-textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask a question about your documents…"
          rows={1}
          disabled={loading}
        />

        <button
          className={`send-btn ${loading ? "loading" : ""}`}
          onClick={handleSubmit}
          disabled={loading || (!text.trim() && !imageFile)}
        >
          {loading ? <span className="spin">↻</span> : "↑"}
        </button>
      </div>
    </div>
  );
}
