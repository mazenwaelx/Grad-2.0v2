import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import useLocalStorage from './useLocalStorage';
import * as api from '../services/api';

/**
 * Custom hook that owns **all** chat state and business logic.
 *
 * The `Chat` page component becomes a thin rendering shell that
 * delegates to this hook.
 *
 * @returns {object} Chat state and action handlers.
 */
const useChat = () => {
  const { currentUser } = useAuth();
  const [searchParams] = useSearchParams();

  // ── Core state ──────────────────────────────────────────────
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [replyToMessage, setReplyToMessage] = useState(null);
  const [messageFiles, setMessageFiles] = useLocalStorage('messageFiles', {});

  // ── Derived ─────────────────────────────────────────────────
  const currentChat = chats.find((c) => c.chat_id === currentChatId);

  // ── Helpers ─────────────────────────────────────────────────
  const getFilesForMessage = useCallback(
    (chatId, messageIndex) => {
      return messageFiles[chatId]?.[messageIndex] ?? [];
    },
    [messageFiles],
  );

  const storeFilesWithMessage = useCallback(
    (chatId, messageIndex, files) => {
      setMessageFiles((prev) => ({
        ...prev,
        [chatId]: {
          ...(prev[chatId] || {}),
          [messageIndex]: files,
        },
      }));
    },
    [setMessageFiles],
  );

  // ── Actions ─────────────────────────────────────────────────

  const createNewChat = useCallback(async () => {
    const chatId = currentUser.email + '_chat_' + Date.now();
    const newChat = {
      chat_id: chatId,
      user_email: currentUser.email,
      title: 'New Chat',
      messages: [],
      created_at: new Date().toISOString(),
    };
    setChats((prev) => [newChat, ...prev]);
    setCurrentChatId(chatId);
    setMessages([]);
    setUploadedFiles([]);
    setReplyToMessage(null);
  }, [currentUser.email]);

  const loadChat = useCallback(
    async (chatId) => {
      setUploadedFiles([]);
      setReplyToMessage(null);
      setCurrentChatId(chatId);

      try {
        const data = await api.getMessages(chatId);
        const loaded = data.messages || [];

        let userIdx = 0;
        const withFiles = loaded.map((msg) => {
          if (msg.role === 'user') {
            const files = getFilesForMessage(chatId, userIdx);
            userIdx++;
            return { ...msg, attachedFiles: files };
          }
          return msg;
        });
        setMessages(withFiles);
      } catch (error) {
        console.error('Error loading messages:', error);
        setMessages([]);
      }
    },
    [getFilesForMessage],
  );

  const sendMessage = useCallback(
    async (messageText) => {
      if (!messageText.trim() || isTyping) return;

      let message = messageText.trim();

      // Reply context
      if (replyToMessage) {
        const roleLabel =
          replyToMessage.role === 'user' ? 'سؤالي السابق' : 'ردك السابق';
        const preview =
          replyToMessage.content.length > 200
            ? replyToMessage.content.substring(0, 200) + '...'
            : replyToMessage.content;
        message = `بالإشارة إلى ${roleLabel}:\n"${preview}"\n\nسؤالي الجديد: ${message}`;
        setReplyToMessage(null);
      }

      const filesToAttach = [...uploadedFiles];
      const userMsgCount = messages.filter((m) => m.role === 'user').length;

      if (filesToAttach.length > 0) {
        storeFilesWithMessage(currentChatId, userMsgCount, filesToAttach);
      }

      setUploadedFiles([]);

      // Extract display-only message
      let displayMessage = message;
      if (message.includes('بالإشارة إلى')) {
        const parts = message.split('سؤالي الجديد: ');
        displayMessage = parts.length > 1 ? parts[1] : message;
      }

      const userMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: displayMessage,
        attachedFiles: filesToAttach,
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsTyping(true);

      try {
        const data = await api.sendMessage(
          currentUser.email,
          currentChatId,
          message,
        );
        setIsTyping(false);

        const assistantMessage = {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: data.response,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // Auto-title
        const chat = chats.find((c) => c.chat_id === currentChatId);
        if (chat && chat.title === 'New Chat') {
          const title =
            displayMessage.substring(0, 30) +
            (displayMessage.length > 30 ? '...' : '');
          setChats((prev) =>
            prev.map((c) =>
              c.chat_id === currentChatId ? { ...c, title } : c,
            ),
          );
        }
      } catch (error) {
        console.error('Error sending message:', error);
        setIsTyping(false);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Sorry, there was an error processing your request.',
          },
        ]);
      }
    },
    [
      isTyping,
      replyToMessage,
      uploadedFiles,
      messages,
      currentChatId,
      chats,
      currentUser.email,
      storeFilesWithMessage,
    ],
  );

  const handleFileUpload = useCallback(
    async (file) => {
      if (!currentChatId) {
        alert('يرجى إنشاء محادثة جديدة أولاً');
        return false;
      }

      const allowedTypes = [
        '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.png', '.jpg', '.jpeg',
      ];
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
        const result = await api.uploadFile(file, currentChatId);
        if (result.success) {
          const fileInfo = {
            hash: result.file_hash,
            name: file.name,
            size: file.size,
            document_count: result.document_count,
          };
          if (!uploadedFiles.find((f) => f.hash === fileInfo.hash)) {
            setUploadedFiles((prev) => [...prev, fileInfo]);
          }
          return true;
        }
        alert('خطأ في رفع الملف: ' + result.message);
        return false;
      } catch (error) {
        console.error('Error uploading file:', error);
        alert('خطأ في رفع الملف. يرجى المحاولة مرة أخرى.');
        return false;
      }
    },
    [currentChatId, uploadedFiles],
  );

  const removeUploadedFile = useCallback(async (fileHash, index) => {
    try {
      await api.deleteFile(fileHash, currentChatId);
      setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '🗑️ تم حذف الملف' },
      ]);
    } catch (error) {
      console.error('Error removing file:', error);
      alert('خطأ في حذف الملف');
    }
  }, [currentChatId]);

  const deleteChat = useCallback(
    async (chatId) => {
      if (!window.confirm('Are you sure you want to delete this chat?')) return;

      try {
        await api.deleteChat(currentUser.email, chatId);
        setChats((prev) => prev.filter((c) => c.chat_id !== chatId));

        setMessageFiles((prev) => {
          const next = { ...prev };
          delete next[chatId];
          return next;
        });

        if (chatId === currentChatId) {
          const remaining = chats.filter((c) => c.chat_id !== chatId);
          if (remaining.length > 0) {
            await loadChat(remaining[0].chat_id);
          } else {
            await createNewChat();
          }
        }
      } catch (error) {
        console.error('Error deleting chat:', error);
        alert('Failed to delete chat');
      }
    },
    [
      currentUser.email,
      currentChatId,
      chats,
      loadChat,
      createNewChat,
      setMessageFiles,
    ],
  );

  const renameChat = useCallback(async (chatId, newTitle) => {
    if (!newTitle?.trim()) return;

    try {
      await api.renameChat(chatId, newTitle.trim());
      setChats((prev) =>
        prev.map((c) =>
          c.chat_id === chatId ? { ...c, title: newTitle.trim() } : c,
        ),
      );
    } catch (error) {
      console.error('Error renaming chat:', error);
      alert('Failed to rename chat');
    }
  }, []);

  const handleReply = useCallback((content, role) => {
    setReplyToMessage({ content, role });
  }, []);

  const cancelReply = useCallback(() => {
    setReplyToMessage(null);
  }, []);

  // ── Initial chat load ───────────────────────────────────────
  useEffect(() => {
    if (!currentUser?.email) return;

    const loadUserChats = async () => {
      try {
        console.log('Loading chats for user:', currentUser.email);
        const data = await api.getChats(currentUser.email);
        const loaded = data.chats || [];
        setChats(loaded);

        const urlChatId = searchParams.get('chatId');
        if (urlChatId) {
          const existing = loaded.find((c) => c.chat_id === urlChatId);
          if (existing) {
            loadChat(urlChatId);
          } else {
            const newChat = {
              chat_id: urlChatId,
              user_email: currentUser.email,
              title: 'New Chat',
              messages: [],
              created_at: new Date().toISOString(),
            };
            setChats((prev) => [newChat, ...prev]);
            setCurrentChatId(urlChatId);
            setMessages([]);
          }
        } else if (loaded.length === 0) {
          createNewChat();
        } else {
          loadChat(loaded[0].chat_id);
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

  // ── Return ──────────────────────────────────────────────────
  return {
    // State
    chats,
    currentChatId,
    currentChat,
    messages,
    isTyping,
    uploadedFiles,
    replyToMessage,

    // Actions
    createNewChat,
    loadChat,
    sendMessage,
    handleFileUpload,
    removeUploadedFile,
    deleteChat,
    renameChat,
    handleReply,
    cancelReply,
  };
};

export default useChat;
