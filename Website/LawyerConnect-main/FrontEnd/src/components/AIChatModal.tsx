import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { X, Send, Bot, User, Sparkles } from 'lucide-react'

interface Message {
  id: number
  text: string
  sender: 'user' | 'ai'
  timestamp: Date
}

interface AIChatModalProps {
  onClose: () => void
}

export default function AIChatModal({ onClose }: AIChatModalProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! I'm your AI legal assistant. How can I help you today?",
      sender: 'ai',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: messages.length + 1,
      text: input,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages([...messages, userMessage])
    setInput('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: messages.length + 2,
        text: getAIResponse(input),
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
      setIsTyping(false)
    }, 1500)
  }

  const getAIResponse = (userInput: string): string => {
    const lowerInput = userInput.toLowerCase()
    
    if (lowerInput.includes('lawyer') || lowerInput.includes('attorney')) {
      return "I can help you find the perfect lawyer for your needs. What type of legal assistance are you looking for? We have specialists in Criminal Law, Corporate Law, Family Law, Real Estate, Immigration, and Tax Law."
    }
    
    if (lowerInput.includes('book') || lowerInput.includes('appointment')) {
      return "To book an appointment, browse our lawyers, select one that matches your needs, and choose an available time slot. The booking process is quick and secure!"
    }
    
    if (lowerInput.includes('price') || lowerInput.includes('cost') || lowerInput.includes('rate')) {
      return "Our lawyers have different hourly rates based on their experience and specialization. You can filter lawyers by rate when browsing. Most consultations range from $100 to $500 per hour."
    }
    
    if (lowerInput.includes('how') || lowerInput.includes('work')) {
      return "It's simple! 1) Browse our verified lawyers 2) Select a lawyer that fits your needs 3) Book a consultation at your preferred time 4) Meet with your lawyer online or in-person. All payments are secure and you can cancel anytime."
    }
    
    return "I'm here to help! You can ask me about finding lawyers, booking appointments, pricing, or how our platform works. What would you like to know?"
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
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-dark-700 bg-gradient-to-r from-purple-500 to-purple-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">AI Legal Assistant</h2>
              <p className="text-sm text-purple-100">Powered by Estasheer AI</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-xl transition-colors"
          >
            <X className="w-6 h-6 text-white" />
          </button>
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
                  ? 'bg-gradient-to-br from-purple-500 to-purple-700'
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
                  <p className="text-sm leading-relaxed">{message.text}</p>
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
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-700 rounded-xl flex items-center justify-center">
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
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about legal services..."
              className="flex-1 px-4 py-3 bg-white dark:bg-dark-900 border border-gray-200 dark:border-dark-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900 dark:text-white"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-700 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
            <Sparkles className="w-3 h-3 inline mr-1" />
            AI responses are for informational purposes only
          </p>
        </div>
      </motion.div>
    </motion.div>
  )
}
