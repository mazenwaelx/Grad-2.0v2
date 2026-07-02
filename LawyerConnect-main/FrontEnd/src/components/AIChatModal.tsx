import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { X, Send, Bot, User, Sparkles, Upload, FileText, Trash2, Loader, Paperclip } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { apiService } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

interface Message {
  id: number
  text: string
  sender: 'user' | 'ai'
  timestamp: Date
}

interface UploadedFile {
  hash: string
  filename: string
  uploadedAt: string
  documentCount: number
}

interface AIChatModalProps {
  onClose: () => void
}

export default function AIChatModal({ onClose }: AIChatModalProps) {
  const { user } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  
  // Persistent chat ID per user - stores chat history but NOT context
  const [chatId, setChatId] = useState<string>(() => {
    const storageKey = `aiChatId_${user?.email || 'guest'}`;
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      return stored;
    }
    const newChatId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem(storageKey, newChatId);
    return newChatId;
  })
  
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Function to create a new chat (clear modal display but keep old chat in standalone app)
  const createNewChat = () => {
    const newChatId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const storageKey = `aiChatId_${user?.email || 'guest'}`;
    
    // DON'T delete old chat - it should remain visible in standalone app's sidebar
    // Just switch to new chat ID
    
    // Update to new chat ID
    setChatId(newChatId);
    localStorage.setItem(storageKey, newChatId);
    
    // Clear local messages (modal display only)
    setMessages([]);
    setUploadedFiles([]);
    setInput('');
    
    // Show welcome message
    setMessages([{
      id: 1,
      text: "مرحباً! أنا مساعدك القانوني بالذكاء الاصطناعي. كيف يمكنني مساعدتك اليوم؟\n\nHello! I'm your AI legal assistant. How can I help you today?",
      sender: 'ai',
      timestamp: new Date()
    }]);
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    loadChatHistory()
    loadUploadedFiles()
  }, [])

  const loadChatHistory = async () => {
    try {
      const messages = await apiService.getAIChatMessages(chatId)
      if (messages && messages.length > 0) {
        const loadedMessages = messages.map((msg: any, index: number) => ({
          id: index + 1,
          text: msg.text,
          sender: msg.sender,
          timestamp: new Date(msg.timestamp)
        }))
        setMessages(loadedMessages)
      } else {
        // Initialize with welcome message
        setMessages([{
          id: 1,
          text: "مرحباً! أنا مساعدك القانوني بالذكاء الاصطناعي. كيف يمكنني مساعدتك اليوم؟\n\nHello! I'm your AI legal assistant. How can I help you today?",
          sender: 'ai',
          timestamp: new Date()
        }])
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
      // Initialize with welcome message on error
      setMessages([{
        id: 1,
        text: "مرحباً! أنا مساعدك القانوني بالذكاء الاصطناعي. كيف يمكنني مساعدتك اليوم؟\n\nHello! I'm your AI legal assistant. How can I help you today?",
        sender: 'ai',
        timestamp: new Date()
      }])
    }
  }

  const loadUploadedFiles = async () => {
    try {
      const files = await apiService.getAIUploadedFiles()
      setUploadedFiles(files || [])
    } catch (error) {
      console.error('Error loading files:', error)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    try {
      const response = await apiService.uploadAIFile(file)

      if (response.success) {
        await loadUploadedFiles()
        // Add system message about file upload
        const systemMessage: Message = {
          id: messages.length + 1,
          text: `✅ تم رفع الملف: ${file.name}\n✅ File uploaded: ${file.name}`,
          sender: 'ai',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, systemMessage])
      }
    } catch (error: any) {
      console.error('Error uploading file:', error)
      const errorMessage: Message = {
        id: messages.length + 1,
        text: `❌ فشل رفع الملف: ${error.message || 'خطأ غير معروف'}\n❌ File upload failed: ${error.message || 'Unknown error'}`,
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDeleteFile = async (fileHash: string) => {
    try {
      await apiService.deleteAIFile(fileHash)
      await loadUploadedFiles()
    } catch (error) {
      console.error('Error deleting file:', error)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || !user) {
      console.log('Cannot send: input empty or no user', { input, user });
      return;
    }

    // Debug: Check if we have an auth token
    const authToken = localStorage.getItem('authToken');
    console.log('Sending AI chat message:', {
      hasToken: !!authToken,
      user: user?.email,
      chatId,
      messageLength: input.length
    });

    const userMessage: Message = {
      id: messages.length + 1,
      text: input,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages([...messages, userMessage])
    setInput('')
    setIsTyping(true)

    try {
      const response = await apiService.sendAIChatMessage(input, chatId)

      const aiMessage: Message = {
        id: messages.length + 2,
        text: response.response,
        sender: 'ai',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, aiMessage])

      // Auto-update chat title with the user's question (first 50 chars)
      try {
        const title = userMessage.text.substring(0, 50) + (userMessage.text.length > 50 ? '...' : '');
        await apiService.renameAIChat(chatId, title);
        console.log('Chat title auto-updated to:', title);
      } catch (error) {
        console.error('Error auto-updating chat title:', error);
        // Don't fail the whole message send if rename fails
      }

      // Check if files were removed by the AI
      if (response.filesRemoved) {
        await loadUploadedFiles()
      }
    } catch (error: any) {
      console.error('Error sending message:', error)
      console.error('Full error details:', {
        message: error.message,
        stack: error.stack,
        hasToken: !!localStorage.getItem('authToken')
      });
      const errorMessage: Message = {
        id: messages.length + 2,
        text: `❌ عذراً، حدث خطأ في معالجة رسالتك. يرجى المحاولة مرة أخرى.\n❌ Sorry, there was an error processing your message. Please try again.\n\nError: ${error.message}`,
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl h-[600px] bg-white dark:bg-dark-900 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-dark-700 bg-gradient-to-r from-primary-600 to-primary-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">AI Legal Assistant</h2>
              <p className="text-sm text-primary-100">Powered by Estasheer AI</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={createNewChat}
              className="p-2 hover:bg-white/20 rounded-xl transition-colors group"
              title="Start New Chat"
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button
              onClick={() => {
                // Pass user info to original AI for auto-login
                const url = new URL('http://localhost:3000');
                url.searchParams.set('chatId', chatId);
                if (user) {
                  url.searchParams.set('userEmail', user.email);
                  url.searchParams.set('userName', user.fullName); // Use fullName instead of name
                }
                window.location.href = url.toString();
              }}
              className="p-2 hover:bg-white/20 rounded-xl transition-colors group"
              title="Open Full Screen AI Chat"
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-xl transition-colors"
            >
              <X className="w-6 h-6 text-white" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${message.sender === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                message.sender === 'ai'
                  ? 'bg-gradient-to-br from-primary-500 to-primary-600'
                  : 'bg-gradient-to-br from-primary-500 to-primary-700'
              }`}>
                {message.sender === 'ai' ? (
                  <Bot className="w-5 h-5 text-white" />
                ) : (
                  <User className="w-5 h-5 text-white" />
                )}
              </div>
              <div className={`flex-1 max-w-[80%] ${message.sender === 'user' ? 'flex justify-end' : ''}`}>
                <div className={`px-4 py-3 rounded-2xl ${
                  message.sender === 'ai'
                    ? 'bg-gray-100 dark:bg-dark-800 text-gray-900 dark:text-white'
                    : 'bg-gradient-to-r from-primary-500 to-primary-700 text-white'
                }`}>
                  {message.sender === 'ai' ? (
                    <div className="text-sm leading-relaxed prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0 prose-headings:my-2">
                      <ReactMarkdown>{message.text}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm leading-relaxed">{message.text}</p>
                  )}
                  <p className={`text-xs mt-1 ${
                    message.sender === 'ai'
                      ? 'text-gray-500 dark:text-gray-400'
                      : 'text-white/70'
                  }`}>
                    {message.timestamp.toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}

          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-3"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="px-4 py-3 bg-gray-100 dark:bg-dark-800 rounded-2xl">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-6 border-t border-gray-200 dark:border-dark-700 bg-gray-50 dark:bg-dark-800">
          {/* Uploaded Files */}
          {uploadedFiles.length > 0 && (
            <div className="mb-4 p-3 bg-white dark:bg-dark-900 rounded-xl border border-gray-200 dark:border-dark-700">
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Uploaded Files:</div>
              <div className="space-y-2">
                {uploadedFiles.map((file) => (
                  <div key={file.hash} className="flex items-center justify-between bg-gray-50 dark:bg-dark-800 px-3 py-2 rounded-lg">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-primary-500" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">{file.filename}</span>
                      <span className="text-xs text-gray-500">({file.documentCount} docs)</span>
                    </div>
                    <button
                      onClick={() => handleDeleteFile(file.hash)}
                      className="p-1 hover:bg-red-100 dark:hover:bg-red-900/20 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.docx,.xlsx,.xls,.png,.jpg,.jpeg"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="px-4 py-3 bg-white dark:bg-dark-900 border border-gray-200 dark:border-dark-700 rounded-xl hover:bg-gray-50 dark:hover:bg-dark-800 transition-colors disabled:opacity-50"
              title="Upload document (PDF, DOCX, Excel, Images)"
            >
              <Upload className={`w-5 h-5 text-primary-500 ${isUploading ? 'animate-bounce' : ''}`} />
            </button>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="اسأل عن القانون المصري... | Ask about Egyptian law..."
              className="flex-1 px-4 py-3 bg-white dark:bg-dark-900 border border-gray-200 dark:border-dark-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white"
              disabled={isTyping}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
            <Sparkles className="w-3 h-3 inline mr-1" />
            Powered by Egyptian Legal AI - Responses are for informational purposes only
          </p>
        </div>
      </motion.div>
    </motion.div>
  )
}
