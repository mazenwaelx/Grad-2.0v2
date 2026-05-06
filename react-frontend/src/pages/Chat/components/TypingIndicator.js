import React from 'react';
import './TypingIndicator.css';

const TypingIndicator = () => {
  return (
    <div className="message assistant-message typing-indicator">
      <div className="message-content">
        <span className="dot"></span>
        <span className="dot"></span>
        <span className="dot"></span>
      </div>
    </div>
  );
};

export default TypingIndicator;
