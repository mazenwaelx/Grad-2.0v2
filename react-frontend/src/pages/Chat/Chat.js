import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import ThemeToggle from '../../components/ThemeToggle';
import Sidebar from './components/Sidebar';
import MessageList from './components/MessageList';
import InputArea from './components/InputArea';
import EmptyState from './components/EmptyState';
import * as api from '../../services/api';
import './Chat.css';

const Chat = () => {
  const { currentUser } = useAuth();
  const [searchParams] = useSearchParams();
  
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [replyToMessage, setReplyToMessage] = useState(null);
  const [messageFiles, setMessageFiles] = useState(() => {
    try {
      const stored = localStorage.getItem('messageFiles');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });

  // Save message files to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('messageFiles', JSON.stringify(messageFiles));
  }, [messageFiles]);

  const createNewChat = useCallback(async () => {
    const chatId = currentUser.email + '_chat_' + Date.now();
    
    const newChat = {
      chat_id: chatId,
      user_email: currentUser.email,
      title: 'New Chat',
      messages: [],
      created_at: new Date().toISOString()
    };
    
    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(chatId);
    setMessages([]);
    setUploadedFiles([]);
    setReplyToMessage(null);
  }, [currentUser.email]);

  const getFilesForMessage = useCallback((chatId, messageIndex) => {
    if (!messageFiles[chatId] || !messageFiles[chatId][messageIndex]) {
      return [];
    }
    return messageFiles[chatId][messageIndex];
  }, [messageFiles]);

  const loadChat = useCallback(async (chatId) => {
    setUploadedFiles([]);
    setReplyToMessage(null);
    setCurrentChatId(chatId);
    
    try {
      const data = await api.getMessages(chatId);
      const loadedMessages = data.messages || [];
      
      // Add file info to user messages
      let userMessageIndex = 0;
      const messagesWithFiles = loadedMessages.map((msg) => {
        if (msg.role === 'user') {
          const files = getFilesForMessage(chatId, userMessageIndex);
          userMessageIndex++;
          return { ...msg, attachedFiles: files };
        }
        return msg;
      });
      
      setMessages(messagesWithFiles);
    } catch (error) {
      console.error('Error loading messages:', error);
      setMessages([]);
    }
  }, [getFilesForMessage]);

  useEffect(() => {
    // Don't load chats until we have a current user
    if (!currentUser || !currentUser.email) {
      console.log('Waiting for user authentication...');
      return;
    }

    const loadUserChats = async () => {
      try {
        console.log('Loading chats for user:', currentUser.email);
        const data = await api.getChats(currentUser.email);
        const loadedChats = data.chats || [];
        setChats(loadedChats);
        
        // Check if chatId is in URL params (coming from website modal)
        const urlChatId = searchParams.get('chatId');
        
        if (urlChatId) {
          console.log('Loading chat from URL:', urlChatId);
          // Use the chat ID from URL
          const existingChat = loadedChats.find(c => c.chat_id === urlChatId);
          if (existingChat) {
            loadChat(urlChatId);
          } else {
            // Create new chat with this ID
            const newChat = {
              chat_id: urlChatId,
              user_email: currentUser.email,
              title: 'New Chat',
              messages: [],
              created_at: new Date().toISOString()
            };
            setChats(prev => [newChat, ...prev]);
            setCurrentChatId(urlChatId);
            setMessages([]);
          }
        } else if (loadedChats.length === 0) {
          console.log('No chats found, creating new chat');
          createNewChat();
        } else {
          console.log('Loading most recent chat');
          loadChat(loadedChats[0].chat_id);
        }
      } catch (error) {
        console.error('Error loading chats:', error);
        setChats([]);
        createNewChat();
      }
    };

    loadUserChats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser?.email, searchParams]);

  const storeFilesWithMessage = (chatId, messageIndex, files) => {
    setMessageFiles(prev => ({
      ...prev,
      [chatId]: {
        ...(prev[chatId] || {}),
        [messageIndex]: files
      }
    }));
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || isTyping) return;
    
    let message = messageText.trim();
    
    // If replying to a message, prepend context
    if (replyToMessage) {
      const roleLabel = replyToMessage.role === 'user' ? 'سؤالي السابق' : 'ردك السابق';
      const contextPreview = replyToMessage.content.length > 200 
        ? replyToMessage.content.substring(0, 200) + '...' 
        : replyToMessage.content;
      
      message = `بالإشارة إلى ${roleLabel}:\n"${contextPreview}"\n\nسؤالي الجديد: ${message}`;
      setReplyToMessage(null);
    }
    
    const filesToAttach = [...uploadedFiles];
    const userMessageCount = messages.filter(m => m.role === 'user').length;
    
    // Store files with this message
    if (filesToAttach.length > 0) {
      storeFilesWithMessage(currentChatId, userMessageCount, filesToAttach);
    }
    
    setUploadedFiles([]);
    
    // Extract display message
    let displayMessage = message;
    if (message.includes('بالإشارة إلى')) {
      const parts = message.split('سؤالي الجديد: ');
      displayMessage = parts.length > 1 ? parts[1] : message;
    }
    
    // Add user message to UI
    const userMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: displayMessage,
      attachedFiles: filesToAttach
    };
    setMessages(prev => [...prev, userMessage]);
    
    setIsTyping(true);
    
    try {
      const data = await api.sendMessage(currentUser.email, currentChatId, message);

      setIsTyping(false);

      // Add assistant response
      const assistantMessage = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: data.response
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Update chat title if new chat
      const chat = chats.find(c => c.chat_id === currentChatId);
      if (chat && chat.title === 'New Chat') {
        const title = displayMessage.substring(0, 30) + (displayMessage.length > 30 ? '...' : '');
        setChats(prev => prev.map(c =>
          c.chat_id === currentChatId ? { ...c, title } : c
        ));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setIsTyping(false);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error processing your request.'
      }]);
    }
  };

  const handleFileUpload = async (file) => {
    if (!currentChatId) {
      alert('يرجى إنشاء محادثة جديدة أولاً');
      return false;
    }
    
    const allowedTypes = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.png', '.jpg', '.jpeg'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExt)) {
      alert('نوع الملف غير مدعوم. الأنواع المدعومة: PDF, DOCX, Excel, PNG, JPG');
      return false;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      alert('حجم الملف كبير جداً. الحد الأقصى 10 ميجابايت');
      return false;
    }
    
    try {
      const result = await api.uploadFile(file);

      if (result.success) {
        const fileInfo = {
          hash: result.file_hash,
          name: file.name,
          size: file.size,
          document_count: result.document_count
        };

        if (!uploadedFiles.find(f => f.hash === fileInfo.hash)) {
          setUploadedFiles(prev => [...prev, fileInfo]);
        }
        return true;
      } else {
        alert('خطأ في رفع الملف: ' + result.message);
        return false;
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('خطأ في رفع الملف. يرجى المحاولة مرة أخرى.');
      return false;
    }
  };

  const removeUploadedFile = async (fileHash, index) => {
    try {
      await api.deleteFile(fileHash);
      setUploadedFiles(prev => prev.filter((_, i) => i !== index));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '🗑️ تم حذف الملف'
      }]);
    } catch (error) {
      console.error('Error removing file:', error);
      alert('خطأ في حذف الملف');
    }
  };

  const deleteChat = useCallback(async (chatId) => {
    if (!window.confirm('Are you sure you want to delete this chat?')) {
      return;
    }

    try {
      await api.deleteChat(currentUser.email, chatId);
      setChats(prev => prev.filter(c => c.chat_id !== chatId));

      // Remove message-file associations
      setMessageFiles(prev => {
        const newFiles = { ...prev };
        delete newFiles[chatId];
        return newFiles;
      });

      if (chatId === currentChatId) {
        const remainingChats = chats.filter(c => c.chat_id !== chatId);
        if (remainingChats.length > 0) {
          await loadChat(remainingChats[0].chat_id);
        } else {
          await createNewChat();
        }
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
      alert('Failed to delete chat');
    }
  }, [currentUser.email, currentChatId, chats, loadChat, createNewChat]);

  const renameChat = useCallback(async (chatId, newTitle) => {
    if (!newTitle || newTitle.trim() === '') return;

    try {
      await api.renameChat(chatId, newTitle.trim());
      setChats(prev => prev.map(c =>
        c.chat_id === chatId ? { ...c, title: newTitle.trim() } : c
      ));
    } catch (error) {
      console.error('Error renaming chat:', error);
      alert('Failed to rename chat');
    }
  }, []);

  const handleReply = (content, role) => {
    setReplyToMessage({ content, role });
  };

  const cancelReply = () => {
    setReplyToMessage(null);
  };

  const currentChat = chats.find(c => c.chat_id === currentChatId);

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
          <h3 id="currentChatTitle">{currentChat?.title || 'Egyptian Legal Assistant'}</h3>
          <div className="header-actions">
            <ThemeToggle />
            <button 
              className="rename-current-btn"
              onClick={() => {
                const newTitle = prompt('Enter new chat title:', currentChat?.title);
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
