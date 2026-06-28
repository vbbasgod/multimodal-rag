const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

async function handleResponse(res) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export async function sendMessage(payload) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  form.append("metadata", JSON.stringify({ source: file.name }));

  const res = await fetch(`${BASE_URL}/ingest/file`, {
    method: "POST",
    body: form,
  });
  return handleResponse(res);
}

export async function ingestText(content, metadata = {}) {
  const res = await fetch(`${BASE_URL}/ingest/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, metadata }),
  });
  return handleResponse(res);
}

export async function healthCheck() {
  const res = await fetch(`${BASE_URL}/health`);
  return handleResponse(res);
}

export async function getMetrics() {
  const res = await fetch(`${BASE_URL}/metrics`);
  return handleResponse(res);
}
