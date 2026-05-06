import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Calendar, Clock, CheckCircle, XCircle, AlertCircle, CreditCard, MessageCircle, Star, Bell } from 'lucide-react'
import { apiService } from '../services/api'
import type { BookingResponseDto, NotificationResponseDto, PaymentSessionResponseDto } from '../types'
import ChatModal from '../components/ChatModal'
import ReviewModal from '../components/ReviewModal'
import PaymentModal from '../components/PaymentModal'

type Tab = 'appointments' | 'payments' | 'notifications'

export default function UserDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('appointments')
  const [bookings, setBookings] = useState<BookingResponseDto[]>([])
  const [payments, setPayments] = useState<PaymentSessionResponseDto[]>([])
  const [notifications, setNotifications] = useState<NotificationResponseDto[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'pending' | 'confirmed' | 'completed' | 'cancelled'>('all')

  // Modals
  const [chatBooking, setChatBooking] = useState<BookingResponseDto | null>(null)
  const [reviewBooking, setReviewBooking] = useState<BookingResponseDto | null>(null)
  const [payBooking, setPayBooking] = useState<BookingResponseDto | null>(null)

  useEffect(() => {
    loadTabData(activeTab)
  }, [activeTab])

  const loadTabData = async (tab: Tab) => {
    setIsLoading(true)
    try {
      switch (tab) {
        case 'appointments':
          // Check cache first (2 minute TTL)
          const cachedBookings = sessionStorage.getItem('user_bookings_cache')
          const cacheTimestamp = sessionStorage.getItem('user_bookings_cache_timestamp')
          const CACHE_TTL = 2 * 60 * 1000 // 2 minutes
          
          if (cachedBookings && cacheTimestamp) {
            const age = Date.now() - parseInt(cacheTimestamp)
            if (age < CACHE_TTL) {
              setBookings(JSON.parse(cachedBookings))
              setIsLoading(false)
              return
            }
          }
          
          const bookingsData = await apiService.getUserBookings()
          setBookings(bookingsData)
          sessionStorage.setItem('user_bookings_cache', JSON.stringify(bookingsData))
          sessionStorage.setItem('user_bookings_cache_timestamp', Date.now().toString())
          break
        case 'payments':
          setPayments(await apiService.getUserPayments())
          break
        case 'notifications':
          setNotifications(await apiService.getNotifications())
          break
      }
    } catch (error) {
      console.error(`Failed to load ${tab}:`, error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleMarkNotifRead = async (id: number) => {
    try {
      await apiService.markNotificationRead(id)
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, isRead: true } : n))
    } catch { /* silently fail */ }
  }

  const handleDeleteNotif = async (id: number) => {
    try {
      await apiService.deleteNotification(id)
      setNotifications(prev => prev.filter(n => n.id !== id))
    } catch { /* silently fail */ }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed': return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'pending': return <AlertCircle className="w-5 h-5 text-yellow-500" />
      case 'cancelled': return <XCircle className="w-5 h-5 text-red-500" />
      case 'completed': return <CheckCircle className="w-5 h-5 text-blue-500" />
      default: return <Clock className="w-5 h-5 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
      case 'pending': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
      case 'cancelled': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
      case 'completed': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
      default: return 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400'
    }
  }

  const filteredBookings = bookings.filter(b => filter === 'all' || b.status.toLowerCase() === filter)

  const tabs = [
    { id: 'appointments' as Tab, label: 'Appointments', icon: Calendar },
    { id: 'payments' as Tab, label: 'Payments', icon: CreditCard },
    { id: 'notifications' as Tab, label: 'Notifications', icon: Bell },
  ]

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-4xl font-display font-bold text-gray-900 dark:text-white mb-2">My Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage your appointments, payments, and notifications</p>
        </motion.div>

        {/* Tabs */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="flex flex-wrap gap-3 mb-8">
          {tabs.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all ${
                activeTab === tab.id ? 'bg-primary-500 text-white shadow-lg' : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700'
              }`}>
              <tab.icon className="w-4 h-4" /> {tab.label}
            </button>
          ))}
        </motion.div>

        {/* ========== APPOINTMENTS TAB ========== */}
        {activeTab === 'appointments' && (
          <>
            {/* Filters */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex flex-wrap gap-3 mb-8">
              {['all', 'pending', 'confirmed', 'completed', 'cancelled'].map((status) => (
                <button key={status} onClick={() => setFilter(status as any)}
                  className={`px-6 py-2.5 rounded-xl font-medium transition-all ${
                    filter === status ? 'bg-primary-500 text-white shadow-lg' : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700'
                  }`}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </motion.div>

            {isLoading ? (
              <div className="text-center py-12">
                <div className="inline-block w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
                <p className="mt-4 text-gray-600 dark:text-gray-400">Loading appointments...</p>
              </div>
            ) : filteredBookings.length === 0 ? (
              <div className="text-center py-12 bg-white dark:bg-dark-800 rounded-2xl">
                <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">No appointments found</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredBookings.map((booking, index) => (
                  <motion.div key={booking.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}
                    className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg p-6 hover:shadow-xl transition-all">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-start gap-4">
                          <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center text-white font-bold flex-shrink-0">
                            {booking.lawyerName?.[0] || 'L'}
                          </div>
                          <div className="flex-1">
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">{booking.lawyerName || 'Lawyer'}</h3>
                            <p className="text-sm text-primary-600 dark:text-primary-400 mb-3">{booking.lawyerSpecialization || 'Legal Consultation'}</p>
                            <div className="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
                              <div className="flex items-center gap-2">
                                <Calendar className="w-4 h-4" />
                                <span>{new Date(booking.date).toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4" />
                                <span>{new Date(booking.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                              </div>
                              {booking.priceSnapshot > 0 && (
                                <div className="flex items-center gap-2">
                                  <CreditCard className="w-4 h-4" />
                                  <span>{booking.priceSnapshot} EGP</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-3">
                        <span className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium ${getStatusColor(booking.status)}`}>
                          {getStatusIcon(booking.status)} {booking.status}
                        </span>
                        <span className={`text-sm px-3 py-1 rounded-lg ${
                          booking.paymentStatus === 'Paid' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400'
                        }`}>
                          Payment: {booking.paymentStatus}
                        </span>

                        {/* Action Buttons */}
                        <div className="flex flex-wrap gap-2">
                          {/* Pay button — for pending + unpaid */}
                          {booking.status.toLowerCase() === 'pending' && booking.paymentStatus.toLowerCase() !== 'paid' && (
                            <button onClick={() => setPayBooking(booking)}
                              className="px-3 py-1.5 text-xs bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors flex items-center gap-1">
                              <CreditCard className="w-3 h-3" /> Pay Now
                            </button>
                          )}
                          {/* Chat button — for confirmed or completed */}
                          {['confirmed', 'completed'].includes(booking.status.toLowerCase()) && (
                            <button onClick={() => setChatBooking(booking)}
                              className="px-3 py-1.5 text-xs bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors flex items-center gap-1">
                              <MessageCircle className="w-3 h-3" /> Chat
                            </button>
                          )}
                          {/* Review button — for completed only */}
                          {booking.status.toLowerCase() === 'completed' && (
                            <button onClick={() => setReviewBooking(booking)}
                              className="px-3 py-1.5 text-xs bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-medium transition-colors flex items-center gap-1">
                              <Star className="w-3 h-3" /> Review
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </>
        )}

        {/* ========== PAYMENTS TAB ========== */}
        {activeTab === 'payments' && (
          <div>
            {isLoading ? (
              <div className="text-center py-12">
                <div className="inline-block w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : payments.length === 0 ? (
              <div className="text-center py-12 bg-white dark:bg-dark-800 rounded-2xl">
                <CreditCard className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">No payment history</p>
              </div>
            ) : (
              <div className="space-y-4">
                {payments.map((payment, index) => (
                  <motion.div key={payment.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}
                    className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg p-5 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Booking #{payment.bookingId}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{new Date(payment.createdAt).toLocaleDateString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900 dark:text-white">{payment.amount} EGP</p>
                      <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                        payment.status.toLowerCase() === 'paid' || payment.status.toLowerCase() === 'completed'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                      }`}>{payment.status}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ========== NOTIFICATIONS TAB ========== */}
        {activeTab === 'notifications' && (
          <div>
            {isLoading ? (
              <div className="text-center py-12">
                <div className="inline-block w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="text-center py-12 bg-white dark:bg-dark-800 rounded-2xl">
                <Bell className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">No notifications</p>
              </div>
            ) : (
              <div className="space-y-3">
                {notifications.map((notif, index) => (
                  <motion.div key={notif.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.03 }}
                    className={`bg-white dark:bg-dark-800 rounded-2xl shadow-lg p-5 flex items-start justify-between gap-4 transition-all ${
                      !notif.isRead ? 'border-l-4 border-primary-500' : ''
                    }`}>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 dark:text-white">{notif.title}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{notif.message}</p>
                      <p className="text-xs text-gray-400 mt-2">{new Date(notif.createdAt).toLocaleString()}</p>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      {!notif.isRead && (
                        <button onClick={() => handleMarkNotifRead(notif.id)}
                          className="px-3 py-1.5 text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded-lg hover:bg-primary-200 dark:hover:bg-primary-900/50 transition-colors">
                          Mark Read
                        </button>
                      )}
                      <button onClick={() => handleDeleteNotif(notif.id)}
                        className="px-3 py-1.5 text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors">
                        Delete
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ========== MODALS ========== */}
      <AnimatePresence>
        {chatBooking && (
          <ChatModal
            bookingId={chatBooking.id}
            otherPartyName={chatBooking.lawyerName || 'Lawyer'}
            onClose={() => setChatBooking(null)}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {reviewBooking && (
          <ReviewModal
            bookingId={reviewBooking.id}
            lawyerId={reviewBooking.lawyerId}
            lawyerName={reviewBooking.lawyerName || 'Lawyer'}
            onClose={() => setReviewBooking(null)}
            onSuccess={() => loadTabData('appointments')}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {payBooking && (
          <PaymentModal
            bookingId={payBooking.id}
            amount={payBooking.priceSnapshot || 0}
            lawyerName={payBooking.lawyerName || 'Lawyer'}
            onClose={() => setPayBooking(null)}
            onSuccess={() => loadTabData('appointments')}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
