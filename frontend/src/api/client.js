const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function parseError(resp) {
  let detail = `HTTP ${resp.status}`;
  try {
    const body = await resp.json();
    detail = body.detail || detail;
  } catch {}
  return new Error(detail);
}

async function handleResponse(resp) {
  if (!resp.ok) throw await parseError(resp);
  return resp.json();
}

/* ─── Chat ───────────────────────────────────────────────── */

export async function sendChatMessage(query, sessionId, useSearch) {
  const resp = await fetch(`${BASE_URL}/api/v1/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId, use_search: useSearch }),
  });
  return handleResponse(resp);
}

/**
 * Async generator that yields parsed SSE event objects.
 * Yields: { type: 'token'|'progress'|'done'|'error', ... }
 */
export async function* streamChatMessage(query, sessionId, useSearch) {
  const resp = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId, use_search: useSearch }),
  });

  if (!resp.ok) throw await parseError(resp);

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by \n\n
      const frames = buffer.split('\n\n');
      buffer = frames.pop() ?? '';

      for (const frame of frames) {
        for (const line of frame.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              yield JSON.parse(line.slice(6));
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/* ─── Documents ──────────────────────────────────────────── */

/**
 * Upload a file with optional progress callback (0–100).
 * Uses XMLHttpRequest to support upload progress events.
 */
export function uploadDocument(file, onProgress) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE_URL}/api/v1/documents/upload`);

    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });
    }

    xhr.onload = () => {
      try {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(data);
        } else {
          reject(new Error(data.detail || `HTTP ${xhr.status}`));
        }
      } catch {
        reject(new Error(`HTTP ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error('网络错误，请检查后端服务是否运行'));
    xhr.send(formData);
  });
}

export async function getHistory(sessionId, limit = 20) {
  const resp = await fetch(
    `${BASE_URL}/api/v1/chat/history/${encodeURIComponent(sessionId)}?limit=${limit}`
  );
  return handleResponse(resp);
}

export async function listDocuments(page = 1, pageSize = 10) {
  const resp = await fetch(
    `${BASE_URL}/api/v1/documents/list?page=${page}&page_size=${pageSize}`
  );
  return handleResponse(resp);
}

export async function deleteDocument(fileId) {
  const resp = await fetch(`${BASE_URL}/api/v1/documents/${fileId}`, {
    method: 'DELETE',
  });
  return handleResponse(resp);
}
