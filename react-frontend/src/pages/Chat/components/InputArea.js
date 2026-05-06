import { useState, useRef } from 'react';
import './InputArea.css';

const InputArea = ({
  onSendMessage,
  onFileUpload,
  uploadedFiles,
  onRemoveFile,
  isTyping,
  replyToMessage,
  onCancelReply
}) => {
  const [message, setMessage] = useState('');
  const [uploading, setUploading] = useState(false);
  const [ripple, setRipple] = useState(null);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (message.trim() && !isTyping) {
      onSendMessage(message);
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextareaChange = (e) => {
    setMessage(e.target.value);
    // Auto-resize
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploading(true);
      await onFileUpload(file);
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleSendClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    setRipple({
      x: e.clientX - rect.left - size / 2,
      y: e.clientY - rect.top - size / 2,
      size,
    });
    setTimeout(() => setRipple(null), 600);
    handleSubmit();
  };

  return (
    <div className="input-container">
      {replyToMessage && (
        <div className="reply-indicator">
          <div className="reply-indicator-content">
            <div className="reply-indicator-icon">↩️</div>
            <div className="reply-indicator-text">
              <div className="reply-indicator-label">
                الرد على: {replyToMessage.role === 'user' ? 'رسالتك' : 'رد المساعد'}
              </div>
              <div className="reply-indicator-preview">
                {replyToMessage.content.length > 80
                  ? replyToMessage.content.substring(0, 80) + '...'
                  : replyToMessage.content}
              </div>
            </div>
          </div>
          <button className="reply-indicator-close" onClick={onCancelReply}>
            ×
          </button>
        </div>
      )}

      <div className="input-wrapper">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf,.docx,.doc,.xlsx,.xls,.jpg,.jpeg"
          style={{ display: 'none' }}
        />
        <button
          className={`file-btn ${uploading ? 'uploading' : ''}`}
          onClick={handleFileClick}
          disabled={uploading}
          title="Upload file (PDF, DOCX, Excel)"
        >
          {uploading ? '⏳' : '📎'}
        </button>

        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about Egyptian labor law..."
          rows="1"
        />

        <button
          className={`send-btn ${isTyping ? 'loading' : ''}`}
          style={{ position: 'relative', overflow: 'hidden' }}
          onClick={handleSendClick}
          disabled={isTyping || !message.trim()}
        >
          {ripple && (
            <span
              style={{
                position: 'absolute',
                borderRadius: '50%',
                background: 'rgba(255, 255, 255, 0.5)',
                transform: 'scale(0)',
                animation: 'ripple 0.6s ease-out',
                pointerEvents: 'none',
                width: ripple.size,
                height: ripple.size,
                left: ripple.x,
                top: ripple.y,
              }}
            />
          )}
          Send 🚀
        </button>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="uploaded-files">
          {uploadedFiles.map((file, index) => (
            <div
              key={file.hash}
              className="file-tag"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <span>📄 {file.name}</span>
              <span
                className="remove-file"
                onClick={() => onRemoveFile(file.hash, index)}
                title="حذف الملف"
              >
                ×
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default InputArea;
