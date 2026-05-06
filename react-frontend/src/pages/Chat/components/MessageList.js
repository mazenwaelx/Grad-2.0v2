import { useEffect, useRef } from 'react';
import Message from './Message';
import TypingIndicator from './TypingIndicator';
import './MessageList.css';

const MessageList = ({ messages, isTyping, onReply }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const timer = setTimeout(() => {
      if (containerRef.current) {
        containerRef.current.scrollTo({
          top: containerRef.current.scrollHeight,
          behavior: 'smooth'
        });
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [messages, isTyping]);

  return (
    <div className="message-list" ref={containerRef}>
      {messages.map((message, index) => (
        <Message
          key={message.id ?? `${message.role}-${index}`}
          role={message.role}
          content={message.content}
          attachedFiles={message.attachedFiles}
          onReply={onReply}
          animate={index === messages.length - 1}
        />
      ))}
      {isTyping && <TypingIndicator />}
    </div>
  );
};

export default MessageList;
