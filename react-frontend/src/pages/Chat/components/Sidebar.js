import React from 'react';
import './Sidebar.css';

const Sidebar = React.memo(({
  chats,
  currentChatId,
  userName,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onRenameChat,
  onLogout
}) => {
  const handleRename = (chatId, currentTitle, e) => {
    e.stopPropagation();
    const newTitle = prompt('Enter new chat title:', currentTitle);
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
        <h2>⚖️ Estasher <span className="arabic">استشير</span></h2>
        <div className="user-info">
          <span>{userName}</span>
        </div>
        <button className="new-chat-btn" onClick={onNewChat}>
          ✨ New Chat
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
                title="Rename"
              >
                ✏️
              </button>
              <button 
                className="delete-chat-btn"
                onClick={(e) => handleDelete(chat.chat_id, e)}
                title="Delete"
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <button className="logout-btn" onClick={onLogout}>
          🚪 Logout
        </button>
      </div>
    </div>
  );
});

export default Sidebar;
