/**
 * Centralized API service layer.
 * All HTTP calls go through here so error handling and base URL are in one place.
 */

const BASE = '';  // proxy in package.json forwards to http://localhost:8000

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || `HTTP ${response.status}`;
    const err = new Error(message);
    err.status = response.status;
    err.data = data;
    throw err;
  }
  return data;
}

function jsonPost(path, body) {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// ---------- Auth ----------

export const login = (email, password) =>
  jsonPost('/api/login', { email, password });

export const register = (email, name, password) =>
  jsonPost('/api/register', { email, name, password });

// ---------- Chats ----------

export const getChats = (userEmail) =>
  request(`/api/chats/${encodeURIComponent(userEmail)}`);

export const deleteChat = (userEmail, chatId) =>
  request(`/api/chat/${encodeURIComponent(userEmail)}/${chatId}`, { method: 'DELETE' });

export const renameChat = (chatId, title) =>
  request(`/api/chat/${chatId}/title`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });

// ---------- Messages ----------

export const getMessages = (chatId) =>
  request(`/api/messages/${chatId}`);

export const sendMessage = (userId, chatId, message) =>
  jsonPost('/api/chat', { user_id: userId, chat_id: chatId, message });

// ---------- Files ----------

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return request('/api/upload', { method: 'POST', body: formData });
};

export const deleteFile = (fileHash) =>
  request(`/api/files/${fileHash}`, { method: 'DELETE' });
