import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { X, Send, MessageCircle, Loader } from 'lucide-react'
import { apiService } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import type { ChatMessageResponseDto } from '../types'

interface ChatModalProps {
  bookingId: number
  otherPartyName: string
  onClose: () => void
}

export default function ChatModal({ bookingId, otherPartyName, onClose }: ChatModalProps) {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessageResponseDto[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [loadError, setLoadError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    loadMessages()
    pollRef.current = setInterval(loadMessages, 5000)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [bookingId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadMessages = async () => {
    try {
      const data = await apiService.getChatMessages(bookingId)
      setMessages(data)
      setLoadError('')
    } catch (error) {
      console.error('Failed to load messages:', error)
      setLoadError(error instanceof Error ? error.message : 'Failed to load messages')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || isSending) return

    try {
      setIsSending(true)
      await apiService.sendChatMessage(bookingId, newMessage.trim())
      setNewMessage('')
      await loadMessages()
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setIsSending(false)
    }
  }

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()
    if (isToday) {
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + 
           date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-white dark:bg-dark-800 rounded-3xl w-full max-w-lg h-[600px] shadow-2xl flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-dark-700 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-t-3xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <MessageCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold">{otherPartyName}</h3>
              <p className="text-sm text-white/70">Booking #{bookingId}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/20 rounded-xl transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader className="w-8 h-8 text-primary-500 animate-spin" />
            </div>
          ) : loadError ? (
            <div className="flex flex-col items-center justify-center h-full text-red-400 px-4 text-center">
              <MessageCircle className="w-12 h-12 mb-3" />
              <p className="font-medium">Could not load messages</p>
              <p className="text-sm mt-1">{loadError}</p>
              <button onClick={loadMessages} className="mt-3 px-4 py-2 bg-primary-500 text-white rounded-xl text-sm hover:bg-primary-600 transition-colors">
                Retry
              </button>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <MessageCircle className="w-12 h-12 mb-3" />
              <p className="font-medium">No messages yet</p>
              <p className="text-sm">Send the first message!</p>
            </div>
          ) : (
            messages.map((msg) => {
              const isMe = msg.senderId === user?.id
              return (
                <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                    isMe
                      ? 'bg-primary-500 text-white rounded-br-md'
                      : 'bg-gray-100 dark:bg-dark-700 text-gray-900 dark:text-white rounded-bl-md'
                  }`}>
                    {!isMe && (
                      <p className="text-xs font-medium text-primary-600 dark:text-primary-400 mb-1">
                        {msg.senderName}
                      </p>
                    )}
                    <p className="text-sm leading-relaxed">{msg.message}</p>
                    <p className={`text-[10px] mt-1 ${isMe ? 'text-white/60' : 'text-gray-400'}`}>
                      {formatTime(msg.sentAt)}
                    </p>
                  </div>
                </div>
              )
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSend} className="p-4 border-t border-gray-200 dark:border-dark-700">
          <div className="flex gap-2">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type a message..."
              disabled={isSending}
              className="flex-1 px-4 py-3 bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all text-gray-900 dark:text-white disabled:opacity-50"
            />
            <motion.button
              type="submit"
              disabled={!newMessage.trim() || isSending}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="p-3 bg-primary-500 text-white rounded-2xl hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSending ? <Loader className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </motion.button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  )
}
