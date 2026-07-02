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
      console.log('[useChat] Loading chat:', chatId);
      setUploadedFiles([]);
      setReplyToMessage(null);
      setCurrentChatId(chatId);

      try {
        const data = await api.getMessages(chatId);
        console.log('[useChat] Loaded messages:', data.messages?.length || 0);
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
        console.log('[useChat] Messages set successfully');
      } catch (error) {
        console.error('[useChat] Error loading messages:', error);
        // Don't clear messages on error - keep existing state
        // Only clear if it's a new chat with no messages
        if (messages.length === 0) {
          setMessages([]);
        }
      }
    },
    [getFilesForMessage, messages.length],
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

        // Auto-update chat title with last question
        const title =
          displayMessage.substring(0, 50) +
          (displayMessage.length > 50 ? '...' : '');
        
        try {
          await api.renameChat(currentChatId, title);
          setChats((prev) =>
            prev.map((c) =>
              c.chat_id === currentChatId ? { ...c, title } : c,
            ),
          );
        } catch (error) {
          console.error('Error auto-updating chat title:', error);
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
      if (!window.confirm('هل أنت متأكد من حذف هذه المحادثة؟')) return;

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
        alert('فشل حذف المحادثة');
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
      alert('فشل إعادة تسمية المحادثة');
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
    if (!currentUser?.email) {
      console.log('[useChat] No user email, clearing chat data');
      // Clear all chat data when user logs out or email changes
      setChats([]);
      setCurrentChatId(null);
      setMessages([]);
      setUploadedFiles([]);
      setReplyToMessage(null);
      return;
    }

    const loadUserChats = async () => {
      try {
        console.log('[useChat] Loading chats for user:', currentUser.email);
        const data = await api.getChats(currentUser.email);
        const loaded = data.chats || [];
        console.log('[useChat] Loaded chats:', loaded.length);
        
        // Don't filter chats - API returns all chats for user
        // The messages are loaded separately when chat is selected
        setChats(loaded);

        const urlChatId = searchParams.get('chatId');
        if (urlChatId) {
          console.log('[useChat] Chat ID from URL:', urlChatId);
          const existing = loaded.find((c) => c.chat_id === urlChatId);
          if (existing) {
            console.log('[useChat] Loading existing chat from URL');
            loadChat(urlChatId);
          } else {
            console.log('[useChat] Creating new chat from URL');
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
          console.log('[useChat] No existing chats, creating new');
          createNewChat();
        } else {
          console.log('[useChat] Loading first chat:', loaded[0].chat_id);
          loadChat(loaded[0].chat_id);
        }
      } catch (error) {
        console.error('[useChat] Error loading chats:', error);
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
