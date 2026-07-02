import React from 'react';
import './Sidebar.css';

const Sidebar = React.memo(({
  chats,
  currentChatId,
  userName,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onRenameChat
}) => {
  const handleRename = (chatId, currentTitle, e) => {
    e.stopPropagation();
    const newTitle = prompt('أدخل عنوان المحادثة الجديد:', currentTitle);
    if (newTitle && newTitle.trim() !== '' && newTitle !== currentTitle) {
      onRenameChat(chatId, newTitle);
    }
  };

  const handleDelete = (chatId, e) => {
    e.stopPropagation();
    onDeleteChat(chatId);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>⚖️ Estasheer <span className="arabic">استشير</span></h2>
        <div className="user-info">
          <span>{userName}</span>
        </div>
        <button className="new-chat-btn" onClick={onNewChat}>
          ✨ محادثة جديدة
        </button>
      </div>

      <div className="chats-list">
        {chats.map((chat, index) => (
          <div
            key={chat.chat_id}
            className={`chat-item ${chat.chat_id === currentChatId ? 'active' : ''}`}
            onClick={() => onSelectChat(chat.chat_id)}
            style={{ animationDelay: `${index * 0.05}s` }}
          >
            <div className="chat-item-content">
              <div className="chat-title">{chat.title}</div>
              <div className="chat-preview">
                {new Date(chat.created_at).toLocaleDateString()}
              </div>
            </div>
            <div className="chat-actions">
              <button 
                className="rename-chat-btn"
                onClick={(e) => handleRename(chat.chat_id, chat.title, e)}
                title="إعادة تسمية"
              >
                ✏️
              </button>
              <button 
                className="delete-chat-btn"
                onClick={(e) => handleDelete(chat.chat_id, e)}
                title="حذف"
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <button 
          className="website-btn" 
          onClick={() => window.location.href = 'http://localhost:3002'}
        >
          🏠 العودة للموقع
        </button>
      </div>
    </div>
  );
});

export default Sidebar;
