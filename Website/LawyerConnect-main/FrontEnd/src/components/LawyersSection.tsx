import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Star, MapPin, Briefcase } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { apiService } from '../services/api'
import type { LawyerResponseDto } from '../types'

export default function LawyersSection() {
  const navigate = useNavigate()
  const [lawyers, setLawyers] = useState<LawyerResponseDto[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadFeaturedLawyers()
  }, [])

  const loadFeaturedLawyers = async () => {
    try {
      setIsLoading(true)
      setError('')
      const data = await apiService.getFeaturedLawyers(3)
      setLawyers(data)
    } catch (err) {
      console.error('Failed to load featured lawyers:', err)
      setError('Failed to load lawyers')
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <section id="lawyers" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-display font-bold mb-4">
            <span className="bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
              Meet Our Expert Lawyers
            </span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Connect with verified legal professionals ready to help you
          </p>
        </motion.div>

        {/* Loading State */}
        {isLoading && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white dark:bg-dark-800 rounded-3xl border border-gray-200 dark:border-dark-700 p-8 animate-pulse">
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-20 h-20 bg-gray-200 dark:bg-dark-700 rounded-2xl"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-5 bg-gray-200 dark:bg-dark-700 rounded w-3/4"></div>
                    <div className="h-4 bg-gray-200 dark:bg-dark-700 rounded w-1/2"></div>
                    <div className="h-4 bg-gray-200 dark:bg-dark-700 rounded w-2/3"></div>
                  </div>
                </div>
                <div className="space-y-3 mb-6">
                  <div className="h-4 bg-gray-200 dark:bg-dark-700 rounded"></div>
                  <div className="h-4 bg-gray-200 dark:bg-dark-700 rounded"></div>
                </div>
                <div className="h-12 bg-gray-200 dark:bg-dark-700 rounded-xl"></div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="text-center py-12">
            <p className="text-red-500 dark:text-red-400 mb-4">{error}</p>
            <button 
              onClick={loadFeaturedLawyers}
              className="px-6 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && lawyers.length === 0 && (
          <div className="text-center py-16 bg-white dark:bg-dark-800 rounded-3xl border border-gray-200 dark:border-dark-700">
            <div className="w-20 h-20 bg-primary-100 dark:bg-primary-900/30 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Briefcase className="w-10 h-10 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
              Coming Soon
            </h3>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
              We're currently onboarding verified lawyers. Please check back soon to connect with legal professionals.
            </p>
          </div>
        )}

        {/* Lawyers Grid */}
        {!isLoading && !error && lawyers.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {lawyers.map((lawyer, index) => (
              <motion.div
                key={lawyer.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -5 }}
                className="group bg-white dark:bg-dark-800 rounded-3xl border border-gray-200 dark:border-dark-700 overflow-hidden hover:shadow-2xl transition-all cursor-pointer"
                onClick={() => navigate(`/lawyer/${lawyer.id}`)}
              >
                <div className="p-8">
                  <div className="flex items-start gap-4 mb-6">
                    <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
                      {lawyer.fullName?.[0] || 'L'}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
                        {lawyer.fullName}
                      </h3>
                      <div className="flex flex-wrap gap-1 mb-2">
                        {(lawyer.specializations || []).map((spec) => (
                          <span key={`${lawyer.id}-${spec}`} className="text-xs px-2 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded-lg font-medium">
                            {spec}
                          </span>
                        ))}
                      </div>
                      {lawyer.averageRating > 0 && (
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {lawyer.averageRating.toFixed(1)}
                          </span>
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            ({lawyer.reviewCount || 0} reviews)
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-3 mb-6">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <Briefcase className="w-4 h-4" />
                      <span className="text-sm">{lawyer.experienceYears} years experience</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <MapPin className="w-4 h-4" />
                      <span className="text-sm line-clamp-1">{lawyer.address}</span>
                    </div>
                  </div>

                  <button 
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(`/lawyer/${lawyer.id}`)
                    }}
                    className="w-full py-3 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-xl font-medium hover:shadow-lg transition-all"
                  >
                    View Profile
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* View All Button */}
        {!isLoading && lawyers.length > 0 && (
          <div className="text-center mt-12">
            <button 
              onClick={() => navigate('/lawyers')}
              className="px-8 py-4 bg-white dark:bg-dark-800 text-gray-900 dark:text-white rounded-2xl font-semibold border-2 border-gray-200 dark:border-dark-700 hover:border-primary-500 dark:hover:border-primary-500 transition-all"
            >
              View All Lawyers
            </button>
          </div>
        )}
      </div>
    </section>
  )
}
