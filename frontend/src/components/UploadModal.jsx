import { useState, useRef } from "react";
import { uploadFile, ingestText } from "../services/api";

export default function UploadModal({ onClose }) {
  const [tab, setTab] = useState("file");
  const [files, setFiles] = useState([]);
  const [text, setText] = useState("");
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const dropRef = useRef();

  const handleFiles = (fileList) => {
    setFiles(Array.from(fileList));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  const handleUpload = async () => {
    setUploading(true);
    setError(null);
    setResults([]);

    try {
      if (tab === "file") {
        const uploads = await Promise.all(files.map((f) => uploadFile(f)));
        setResults(uploads);
      } else {
        const result = await ingestText(text);
        setResults([result]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2>Upload Documents</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-tabs">
          {["file", "text"].map((t) => (
            <button
              key={t}
              className={`modal-tab ${tab === t ? "active" : ""}`}
              onClick={() => setTab(t)}
            >
              {t === "file" ? "📄 File" : "✏️ Text"}
            </button>
          ))}
        </div>

        <div className="modal-body">
          {tab === "file" ? (
            <div
              ref={dropRef}
              className={`drop-zone ${files.length ? "has-files" : ""}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => document.getElementById("file-input").click()}
            >
              <input
                id="file-input"
                type="file"
                multiple
                accept=".pdf,.txt,.png,.jpg,.jpeg,.webp"
                style={{ display: "none" }}
                onChange={(e) => handleFiles(e.target.files)}
              />
              {files.length ? (
                <div className="file-list">
                  {files.map((f) => (
                    <div key={f.name} className="file-item">
                      <span>{f.type.includes("image") ? "🖼" : f.type === "application/pdf" ? "📕" : "📄"}</span>
                      <span>{f.name}</span>
                      <span className="file-size">{(f.size / 1024).toFixed(1)} KB</span>
                    </div>
                  ))}
                </div>
              ) : (
                <>
                  <div className="drop-icon">↑</div>
                  <p>Drop files here or click to browse</p>
                  <p className="drop-hint">PDF, PNG, JPG, TXT · up to 50MB</p>
                </>
              )}
            </div>
          ) : (
            <textarea
              className="text-ingest"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste document text here…"
              rows={8}
            />
          )}

          {error && <div className="upload-error">⚠ {error}</div>}

          {results.length > 0 && (
            <div className="upload-results">
              {results.map((r, i) => (
                <div key={i} className="result-item">
                  ✓ {r.chunks_created} chunks indexed · {r.modalities_detected.join(", ")}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button
            className="btn-primary"
            onClick={handleUpload}
            disabled={uploading || (tab === "file" ? !files.length : !text.trim())}
          >
            {uploading ? "Uploading…" : "Upload & Index"}
          </button>
        </div>
      </div>
    </div>
  );
}
