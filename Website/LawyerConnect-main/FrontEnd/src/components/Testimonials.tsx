import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Star, Quote } from 'lucide-react'
import { apiService } from '../services/api'
import type { ReviewResponseDto } from '../types'

export default function Testimonials() {
  const [reviews, setReviews] = useState<ReviewResponseDto[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadFeaturedReviews()
  }, [])

  const loadFeaturedReviews = async () => {
    try {
      setIsLoading(true)
      setError('')
      const data = await apiService.getFeaturedReviews(3)
      setReviews(data)
    } catch (err) {
      console.error('Failed to load featured reviews:', err)
      setError('Failed to load reviews')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section id="testimonials" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-display font-bold mb-4">
            <span className="bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
              What Our Clients Say
            </span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Real reviews from satisfied clients
          </p>
        </motion.div>

        {/* Loading State */}
        {isLoading && (
          <div className="grid md:grid-cols-3 gap-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white dark:bg-dark-800 rounded-3xl p-8 border border-gray-200 dark:border-dark-700 animate-pulse">
                <div className="w-10 h-10 bg-gray-200 dark:bg-dark-700 rounded mb-4"></div>
                <div className="space-y-3 mb-6">
                  <div className="h-4 bg-gray-200 dark:bg-dark-700 rounded"></div>
                  <div className="h-4 bg-gray-200 dark:bg-dark-700 rounded"></div>
                  <div className="h-4 bg-gray-200 dark:bg-dark-700 rounded w-3/4"></div>
                </div>
                <div className="flex gap-1 mb-4">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <div key={s} className="w-5 h-5 bg-gray-200 dark:bg-dark-700 rounded"></div>
                  ))}
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gray-200 dark:bg-dark-700 rounded-full"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 dark:bg-dark-700 rounded w-2/3"></div>
                    <div className="h-3 bg-gray-200 dark:bg-dark-700 rounded w-1/2"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="text-center py-12">
            <p className="text-red-500 dark:text-red-400 mb-4">{error}</p>
            <button 
              onClick={loadFeaturedReviews}
              className="px-6 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && reviews.length === 0 && (
          <div className="text-center py-16 bg-white dark:bg-dark-800 rounded-3xl border border-gray-200 dark:border-dark-700">
            <div className="w-20 h-20 bg-primary-100 dark:bg-primary-900/30 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Quote className="w-10 h-10 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
              Reviews Coming Soon
            </h3>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
              Be the first to share your experience with our legal professionals.
            </p>
          </div>
        )}

        {/* Reviews Grid */}
        {!isLoading && !error && reviews.length > 0 && (
          <div className="grid md:grid-cols-3 gap-8">
            {reviews.map((review, index) => (
              <motion.div
                key={review.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bg-white dark:bg-dark-800 rounded-3xl p-8 border border-gray-200 dark:border-dark-700 hover:shadow-2xl transition-all"
              >
                <Quote className="w-10 h-10 text-primary-500 mb-4" />
                <p className="text-gray-700 dark:text-gray-300 mb-6 leading-relaxed line-clamp-4">
                  "{review.comment}"
                </p>
                <div className="flex items-center gap-1 mb-4">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star 
                      key={star} 
                      className={`w-5 h-5 ${star <= review.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300 dark:text-dark-600'}`} 
                    />
                  ))}
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    {review.userName?.[0] || 'U'}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {review.userName || 'Client'}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      Reviewed {review.lawyerName || 'Lawyer'}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
