import { useState, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import './Message.css';

const Message = ({ role, content, attachedFiles = [], onReply, animate }) => {
  const [copied, setCopied] = useState(false);

  const copyMessage = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = content;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Fallback copy failed:', err);
      }
      document.body.removeChild(textArea);
    }
  };

  const handleReply = () => {
    onReply(content, role);
  };

  return (
    <div 
      className={`message ${role}-message ${animate ? 'animate' : ''}`}
    >
      <div className="message-wrapper">
        {attachedFiles && attachedFiles.length > 0 && role === 'user' && (
          <div className="message-files">
            {attachedFiles.map((file, index) => (
              <div key={index} className="message-file-tag">
                <span className="file-icon">📄</span>
                <span className="file-name">{file.name}</span>
              </div>
            ))}
          </div>
        )}
        <div className="message-content">
          {role === 'assistant' ? (
            <ReactMarkdown>{content}</ReactMarkdown>
          ) : (
            content
          )}
        </div>
      </div>
      <div className="message-actions">
        <button 
          className="reply-btn"
          onClick={handleReply}
          title="Reply to this message"
        >
          ↩️
        </button>
        <button 
          className={`copy-btn ${copied ? 'copied' : ''}`}
          onClick={copyMessage}
          title={copied ? 'Copied!' : 'Copy message'}
        >
          {copied ? '✓' : '📋'}
        </button>
      </div>
    </div>
  );
};

export default memo(Message);
