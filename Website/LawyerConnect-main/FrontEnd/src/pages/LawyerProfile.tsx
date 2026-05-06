import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Briefcase, Calendar, ArrowLeft, CheckCircle, Star, MapPin } from 'lucide-react'
import { apiService } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import type { LawyerResponseDto, ReviewResponseDto } from '../types'
import BookingCalendar from '../components/BookingCalendar'

export default function LawyerProfile() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isLoggedIn } = useAuth()
  const [lawyer, setLawyer] = useState<LawyerResponseDto | null>(null)
  const [reviews, setReviews] = useState<ReviewResponseDto[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showBooking, setShowBooking] = useState(false)

  useEffect(() => {
    if (id) {
      loadLawyer(Number(id))
      loadReviews(Number(id))
    }
  }, [id])

  const loadLawyer = async (lawyerId: number) => {
    try {
      setIsLoading(true)
      const data = await apiService.getLawyerById(lawyerId)
      setLawyer(data)
    } catch (error) {
      console.error('Failed to load lawyer:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadReviews = async (lawyerId: number) => {
    try {
      const data = await apiService.getLawyerReviews(lawyerId, 1, 20)
      setReviews(data)
    } catch {
      // silently fail
    }
  }

  const handleBooking = () => {
    if (!isLoggedIn) {
      alert('Please login to book a consultation')
      return
    }
    setShowBooking(true)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen pt-24 flex items-center justify-center">
        <div className="inline-block w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  if (!lawyer) {
    return (
      <div className="min-h-screen pt-24 flex items-center justify-center">
        <p className="text-gray-600 dark:text-gray-400">Lawyer not found</p>
      </div>
    )
  }

  const avgRating = lawyer.averageRating || (reviews.length > 0 ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length : 0)

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate('/lawyers')}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Lawyers
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Profile */}
          <div className="lg:col-span-2 space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white dark:bg-dark-800 rounded-2xl shadow-xl p-8"
            >
              {/* Header */}
              <div className="flex items-start gap-6 mb-6">
                <div className="w-24 h-24 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl flex items-center justify-center text-white text-3xl font-bold flex-shrink-0">
                  {lawyer.fullName?.[0] || 'L'}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                        {lawyer.fullName}
                      </h1>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {(lawyer.specializations || []).map((spec, i) => (
                          <span key={i} className="text-sm text-primary-600 dark:text-primary-400 font-medium px-2 py-0.5 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
                            {spec}
                          </span>
                        ))}
                      </div>
                    </div>
                    {lawyer.isVerified && (
                      <span className="flex items-center gap-1 px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-sm font-medium rounded-full">
                        <CheckCircle className="w-4 h-4" />
                        Verified
                      </span>
                    )}
                  </div>
                  
                  <div className="flex flex-wrap gap-4 mt-4">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <Briefcase className="w-5 h-5" />
                      <span>{lawyer.experienceYears} years experience</span>
                    </div>
                    {avgRating > 0 && (
                      <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                        <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                        <span className="font-semibold text-gray-900 dark:text-white">
                          {avgRating.toFixed(1)} <span className="text-gray-400 font-normal">({lawyer.reviewCount || reviews.length} reviews)</span>
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Address */}
              <div className="border-t border-gray-200 dark:border-dark-700 pt-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-primary-500" /> Office Address
                </h2>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  {lawyer.address}
                </p>
              </div>

              {/* Expertise */}
              <div className="border-t border-gray-200 dark:border-dark-700 pt-6 mt-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Expertise</h2>
                <div className="flex flex-wrap gap-2">
                  {(lawyer.specializations || []).map((spec, i) => (
                    <span key={i} className="px-4 py-2 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded-xl font-medium">
                      {spec}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Reviews Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white dark:bg-dark-800 rounded-2xl shadow-xl p-8"
            >
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
                <Star className="w-5 h-5 text-yellow-500" /> Client Reviews
                {reviews.length > 0 && (
                  <span className="text-sm font-normal text-gray-400">({reviews.length})</span>
                )}
              </h2>

              {reviews.length === 0 ? (
                <div className="text-center py-8">
                  <Star className="w-12 h-12 text-gray-300 dark:text-dark-600 mx-auto mb-3" />
                  <p className="text-gray-500 dark:text-gray-400">No reviews yet</p>
                </div>
              ) : (
                <div className="space-y-5">
                  {/* Rating Summary */}
                  <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-dark-700 rounded-2xl mb-6">
                    <div className="text-center">
                      <p className="text-4xl font-bold text-gray-900 dark:text-white">{avgRating.toFixed(1)}</p>
                      <div className="flex gap-0.5 justify-center mt-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Star key={star} className={`w-4 h-4 ${star <= Math.round(avgRating) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300 dark:text-dark-600'}`} />
                        ))}
                      </div>
                      <p className="text-xs text-gray-400 mt-1">{reviews.length} reviews</p>
                    </div>
                    <div className="flex-1 space-y-1">
                      {[5, 4, 3, 2, 1].map((star) => {
                        const count = reviews.filter(r => r.rating === star).length
                        const pct = reviews.length > 0 ? (count / reviews.length) * 100 : 0
                        return (
                          <div key={star} className="flex items-center gap-2 text-sm">
                            <span className="w-3 text-gray-500">{star}</span>
                            <div className="flex-1 h-2 bg-gray-200 dark:bg-dark-600 rounded-full overflow-hidden">
                              <div className="h-full bg-yellow-400 rounded-full transition-all" style={{ width: `${pct}%` }} />
                            </div>
                            <span className="w-8 text-xs text-gray-400 text-right">{count}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Individual Reviews */}
                  {reviews.map((review) => (
                    <div key={review.id} className="border-b border-gray-100 dark:border-dark-700 pb-5 last:border-0 last:pb-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center text-white font-semibold text-sm">
                            {review.userName?.[0] || 'U'}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white text-sm">{review.userName || 'Client'}</p>
                            <p className="text-xs text-gray-400">{new Date(review.createdAt).toLocaleDateString()}</p>
                          </div>
                        </div>
                        <div className="flex gap-0.5">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <Star key={star} className={`w-3.5 h-3.5 ${star <= review.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300 dark:text-dark-600'}`} />
                          ))}
                        </div>
                      </div>
                      {review.comment && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed ml-12">{review.comment}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>

          {/* Booking Sidebar */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white dark:bg-dark-800 rounded-2xl shadow-xl p-6 sticky top-24"
            >
              <div className="text-center mb-6">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Book a consultation session
                </p>
              </div>

              {showBooking ? (
                <BookingCalendar
                  lawyerId={lawyer.id}
                  onSuccess={() => {
                    setShowBooking(false)
                    navigate('/dashboard')
                  }}
                  onCancel={() => setShowBooking(false)}
                />
              ) : (
                <button
                  onClick={handleBooking}
                  className="w-full py-3 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
                >
                  <Calendar className="w-5 h-5" />
                  Book Consultation
                </button>
              )}

              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-dark-700 space-y-3">
                <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Instant confirmation</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Secure payment</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Free cancellation</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}
