/**
 * Centralized API service layer.
 *
 * All HTTP calls go through here so error handling and
 * base URL configuration are in one place.
 *
 * @module services/api
 */

/** Base URL — proxy in package.json forwards to http://localhost:8000 */
const BASE = '';

/**
 * Generic HTTP request wrapper.
 *
 * @param   {string}  path     API path (e.g. '/api/health')
 * @param   {object}  options  fetch options
 * @returns {Promise<object>}  Parsed JSON response body
 * @throws  {Error}            Enriched error with `.status` and `.data`
 */
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

/**
 * Shorthand for a JSON POST request.
 *
 * @param   {string}  path  API path
 * @param   {object}  body  Request body (will be JSON-serialized)
 * @returns {Promise<object>}
 */
function jsonPost(path, body) {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// ── Auth ──────────────────────────────────────────────────────────

/** @param {string} email  @param {string} password */
export const login = (email, password) =>
  jsonPost('/api/login', { email, password });

/** @param {string} email  @param {string} name  @param {string} password */
export const register = (email, name, password) =>
  jsonPost('/api/register', { email, name, password });

// ── Chats ─────────────────────────────────────────────────────────

/** @param {string} userEmail  @returns {Promise<{chats: Array}>} */
export const getChats = (userEmail) =>
  request(`/api/chats/${encodeURIComponent(userEmail)}`);

/** @param {string} userEmail  @param {string} chatId */
export const deleteChat = (userEmail, chatId) =>
  request(`/api/chat/${encodeURIComponent(userEmail)}/${chatId}`, {
    method: 'DELETE',
  });

/** @param {string} chatId  @param {string} title */
export const renameChat = (chatId, title) =>
  request(`/api/chat/${chatId}/title`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });

// ── Messages ──────────────────────────────────────────────────────

/** @param {string} chatId  @returns {Promise<{messages: Array}>} */
export const getMessages = (chatId) =>
  request(`/api/messages/${chatId}`);

/**
 * Send a chat message and get the AI response.
 *
 * @param {string} userId   User email or ID
 * @param {string} chatId   Chat session ID
 * @param {string} message  User message text
 * @returns {Promise<{response: string, chat_id: string}>}
 */
export const sendMessage = (userId, chatId, message) =>
  jsonPost('/api/chat', { user_id: userId, chat_id: chatId, message });

// ── Files ─────────────────────────────────────────────────────────

/**
 * Upload a file for processing.
 *
 * @param   {File}  file  Browser File object
 * @returns {Promise<{success: boolean, file_hash?: string, document_count?: number}>}
 */
export const uploadFile = async (file, chatId) => {
  const formData = new FormData();
  formData.append('file', file);
  return request(`/api/upload?chat_id=${encodeURIComponent(chatId)}`, { method: 'POST', body: formData });
};

export const deleteFile = (fileHash, chatId) =>
  request(`/api/files/${fileHash}?chat_id=${encodeURIComponent(chatId)}`, { method: 'DELETE' });
