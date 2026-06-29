import { useAuth } from '../../context/AuthContext';
import ThemeToggle from '../../components/ThemeToggle';
import Sidebar from './components/Sidebar';
import MessageList from './components/MessageList';
import InputArea from './components/InputArea';
import EmptyState from './components/EmptyState';
import useChat from '../../hooks/useChat';
import './Chat.css';

/**
 * Chat page — thin rendering shell.
 *
 * All state management and business logic lives in the `useChat` hook.
 */
const Chat = () => {
  const { currentUser } = useAuth();
  const {
    chats,
    currentChatId,
    currentChat,
    messages,
    isTyping,
    uploadedFiles,
    replyToMessage,
    createNewChat,
    loadChat,
    sendMessage,
    handleFileUpload,
    removeUploadedFile,
    deleteChat,
    renameChat,
    handleReply,
    cancelReply,
  } = useChat();

  return (
    <div className="chat-container">
      <Sidebar
        chats={chats}
        currentChatId={currentChatId}
        userName={currentUser.name}
        onNewChat={createNewChat}
        onSelectChat={loadChat}
        onDeleteChat={deleteChat}
        onRenameChat={renameChat}
      />

      <div className="main-chat">
        <div className="chat-header">
          <h3 id="currentChatTitle">
            {currentChat?.title || 'Egyptian Legal Assistant'}
          </h3>
          <div className="header-actions">
            <ThemeToggle />
            <button
              className="rename-current-btn"
              onClick={() => {
                const newTitle = prompt(
                  'Enter new chat title:',
                  currentChat?.title,
                );
                if (newTitle) {
                  renameChat(currentChatId, newTitle);
                }
              }}
            >
              ✏️ Rename
            </button>
          </div>
        </div>

        <div className="messages-container">
          {messages.length === 0 ? (
            <EmptyState onSuggestionClick={sendMessage} />
          ) : (
            <MessageList
              messages={messages}
              isTyping={isTyping}
              onReply={handleReply}
            />
          )}
        </div>

        <InputArea
          onSendMessage={sendMessage}
          onFileUpload={handleFileUpload}
          uploadedFiles={uploadedFiles}
          onRemoveFile={removeUploadedFile}
          isTyping={isTyping}
          replyToMessage={replyToMessage}
          onCancelReply={cancelReply}
        />
      </div>
    </div>
  );
};

export default Chat;
