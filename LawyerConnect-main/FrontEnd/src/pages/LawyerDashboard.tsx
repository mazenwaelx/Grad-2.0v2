import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Calendar, Clock, CheckCircle, XCircle, AlertCircle, MessageCircle, Star, ThumbsUp, ThumbsDown, TrendingUp } from 'lucide-react'
import { apiService } from '../services/api'
import type { BookingResponseDto, ReviewResponseDto } from '../types'
import ChatModal from '../components/ChatModal'

type Tab = 'appointments' | 'reviews'

export default function LawyerDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('appointments')
  const [bookings, setBookings] = useState<BookingResponseDto[]>([])
  const [reviews, setReviews] = useState<ReviewResponseDto[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'pending' | 'confirmed' | 'completed' | 'cancelled'>('all')
  const [chatBooking, setChatBooking] = useState<BookingResponseDto | null>(null)
  const [lawyerProfile, setLawyerProfile] = useState<any>(null)
  const [actionError, setActionError] = useState<string>('')

  useEffect(() => {
    loadLawyerProfile()
  }, [])

  useEffect(() => {
    loadTabData(activeTab)
  }, [activeTab])

  const loadLawyerProfile = async () => {
    try {
      const profile = await apiService.getMyLawyerProfile()
      setLawyerProfile(profile)
    } catch {
      // silently fail
    }
  }

  const loadTabData = async (tab: Tab) => {
    setIsLoading(true)
    try {
      switch (tab) {
        case 'appointments':
          // Check cache first (1 minute TTL)
          const cachedBookings = sessionStorage.getItem('lawyer_bookings_cache')
          const cacheTimestamp = sessionStorage.getItem('lawyer_bookings_cache_timestamp')
          const CACHE_TTL = 60 * 1000 // 1 minute
          
          if (cachedBookings && cacheTimestamp) {
            const age = Date.now() - parseInt(cacheTimestamp)
            if (age < CACHE_TTL) {
              setBookings(JSON.parse(cachedBookings))
              setIsLoading(false)
              return
            }
          }
          
          const bookingsData = await apiService.getLawyerBookings()
          setBookings(bookingsData)
          sessionStorage.setItem('lawyer_bookings_cache', JSON.stringify(bookingsData))
          sessionStorage.setItem('lawyer_bookings_cache_timestamp', Date.now().toString())
          break
        case 'reviews':
          if (lawyerProfile?.id) {
            setReviews(await apiService.getLawyerReviews(lawyerProfile.id))
          }
          break
      }
    } catch (error) {
      console.error(`Failed to load ${tab}:`, error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdateStatus = async (id: number, status: string) => {
    try {
      setActionError('')
      await apiService.updateBookingStatus(id, status)
      
      // Clear cache after status update
      sessionStorage.removeItem('lawyer_bookings_cache')
      sessionStorage.removeItem('lawyer_bookings_cache_timestamp')
      
      await loadTabData('appointments')
    } catch (error) {
      console.error('Failed to update booking status:', error)
      setActionError(error instanceof Error ? error.message : 'Failed to update booking status')
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

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed': return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'pending': return <AlertCircle className="w-5 h-5 text-yellow-500" />
      case 'cancelled': return <XCircle className="w-5 h-5 text-red-500" />
      case 'completed': return <CheckCircle className="w-5 h-5 text-blue-500" />
      default: return <Clock className="w-5 h-5 text-gray-500" />
    }
  }

  const filteredBookings = bookings.filter(b => filter === 'all' || b.status.toLowerCase() === filter)
  const pendingCount = bookings.filter(b => b.status.toLowerCase() === 'pending').length
  const avgRating = reviews.length > 0 ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length : 0

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-4xl font-display font-bold text-gray-900 dark:text-white mb-2">Lawyer Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage your client consultations</p>
        </motion.div>

        {/* Stats Cards */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg p-5 flex items-center gap-4">
            <div className="w-12 h-12 bg-yellow-100 dark:bg-yellow-900/30 rounded-xl flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{pendingCount}</p>
            </div>
          </div>
          <div className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg p-5 flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-xl flex items-center justify-center">
              <Star className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Rating</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{avgRating > 0 ? avgRating.toFixed(1) : '—'} <span className="text-sm text-gray-400 font-normal">/ 5</span></p>
            </div>
          </div>
          <div className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg p-5 flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Bookings</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{bookings.length}</p>
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex flex-wrap gap-3 mb-8">
          <button onClick={() => setActiveTab('appointments')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all ${activeTab === 'appointments' ? 'bg-primary-500 text-white shadow-lg' : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700'}`}>
            <Calendar className="w-4 h-4" /> Appointments
          </button>
          <button onClick={() => setActiveTab('reviews')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all ${activeTab === 'reviews' ? 'bg-primary-500 text-white shadow-lg' : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700'}`}>
            <Star className="w-4 h-4" /> Reviews ({reviews.length})
          </button>
        </motion.div>

        {/* ========== APPOINTMENTS TAB ========== */}
        {activeTab === 'appointments' && (
          <>
            {/* Action Error */}
            {actionError && (
              <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-xl text-sm flex items-center justify-between">
                <span>{actionError}</span>
                <button onClick={() => setActionError('')} className="ml-2 text-red-500 hover:text-red-700">✕</button>
              </div>
            )}
            {/* Filters */}
            <div className="flex flex-wrap gap-3 mb-6">
              {['all', 'pending', 'confirmed', 'completed', 'cancelled'].map((status) => (
                <button key={status} onClick={() => setFilter(status as any)}
                  className={`px-5 py-2 rounded-xl font-medium text-sm transition-all ${
                    filter === status ? 'bg-primary-500 text-white shadow-lg' : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700'
                  }`}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>

            {isLoading ? (
              <div className="text-center py-12">
                <div className="inline-block w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
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
                            {booking.clientName?.[0] || 'C'}
                          </div>
                          <div>
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white">{booking.clientName || 'Client'}</h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400">{booking.clientEmail}</p>
                            <div className="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400 mt-2">
                              <div className="flex items-center gap-2">
                                <Calendar className="w-4 h-4" />
                                <span>{new Date(booking.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4" />
                                <span>{new Date(booking.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-3">
                        <span className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium ${getStatusColor(booking.status)}`}>
                          {getStatusIcon(booking.status)} {booking.status}
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {booking.status.toLowerCase() === 'pending' && (
                            <>
                              <button onClick={() => handleUpdateStatus(booking.id, 'Confirmed')}
                                className="px-3 py-1.5 text-xs bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors flex items-center gap-1">
                                <ThumbsUp className="w-3 h-3" /> Approve
                              </button>
                              <button onClick={() => handleUpdateStatus(booking.id, 'Cancelled')}
                                className="px-3 py-1.5 text-xs bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors flex items-center gap-1">
                                <ThumbsDown className="w-3 h-3" /> Decline
                              </button>
                            </>
                          )}
                          {booking.status.toLowerCase() === 'confirmed' && (
                            <>
                              <button onClick={() => handleUpdateStatus(booking.id, 'Completed')}
                                className="px-3 py-1.5 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors flex items-center gap-1">
                                <CheckCircle className="w-3 h-3" /> Complete
                              </button>
                              <button onClick={() => setChatBooking(booking)}
                                className="px-3 py-1.5 text-xs bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors flex items-center gap-1">
                                <MessageCircle className="w-3 h-3" /> Chat
                              </button>
                            </>
                          )}
                          {booking.status.toLowerCase() === 'completed' && (
                            <button onClick={() => setChatBooking(booking)}
                              className="px-3 py-1.5 text-xs bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors flex items-center gap-1">
                              <MessageCircle className="w-3 h-3" /> Chat
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

        {/* ========== REVIEWS TAB ========== */}
        {activeTab === 'reviews' && (
          <div>
            {isLoading ? (
              <div className="text-center py-12">
                <div className="inline-block w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : reviews.length === 0 ? (
              <div className="text-center py-12 bg-white dark:bg-dark-800 rounded-2xl">
                <Star className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">No reviews yet</p>
              </div>
            ) : (
              <div className="space-y-4">
                {reviews.map((review, index) => (
                  <motion.div key={review.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}
                    className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-xl flex items-center justify-center text-white font-bold">
                          {review.userName?.[0] || 'U'}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{review.userName || 'Client'}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{new Date(review.createdAt).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <div className="flex gap-0.5">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Star key={star} className={`w-4 h-4 ${star <= review.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300 dark:text-dark-600'}`} />
                        ))}
                      </div>
                    </div>
                    {review.comment && (
                      <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">{review.comment}</p>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chat Modal */}
      <AnimatePresence>
        {chatBooking && (
          <ChatModal
            bookingId={chatBooking.id}
            otherPartyName={chatBooking.clientName || 'Client'}
            onClose={() => setChatBooking(null)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
