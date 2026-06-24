import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search, Briefcase, Star, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { apiService } from '../services/api'
import type { LawyerResponseDto, SpecializationDto } from '../types'

export default function BrowseLawyers() {
  const navigate = useNavigate()
  const [lawyers, setLawyers] = useState<LawyerResponseDto[]>([])
  const [filteredLawyers, setFilteredLawyers] = useState<LawyerResponseDto[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSpecializationId, setSelectedSpecializationId] = useState<number | null>(null)
  const [specializations, setSpecializations] = useState<SpecializationDto[]>([])

  useEffect(() => {
    // Load lawyers and specializations on mount
    loadLawyers()
    loadSpecializations()
  }, [])

  useEffect(() => {
    filterLawyers()
  }, [lawyers, searchTerm, selectedSpecializationId, specializations])

  const loadLawyers = async () => {
    try {
      setIsLoading(true)
      
      // Check sessionStorage cache first
      const cachedLawyers = sessionStorage.getItem('lawyers_cache')
      const cacheTimestamp = sessionStorage.getItem('lawyers_cache_timestamp')
      const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
      
      if (cachedLawyers && cacheTimestamp) {
        const age = Date.now() - Number.parseInt(cacheTimestamp, 10)
        if (age < CACHE_DURATION) {
          // Use cached data
          setLawyers(JSON.parse(cachedLawyers))
          setIsLoading(false)
          return
        }
      }
      
      // Fetch fresh data
      const data = await apiService.getLawyers(1, 100)
      setLawyers(data)
      
      // Cache the data
      sessionStorage.setItem('lawyers_cache', JSON.stringify(data))
      sessionStorage.setItem('lawyers_cache_timestamp', Date.now().toString())
    } catch (error) {
      console.error('Failed to load lawyers:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadSpecializations = async () => {
    try {
      const data = await apiService.getSpecializations()
      setSpecializations(data)
    } catch {
      setSpecializations([
        { id: 1, name: 'Criminal Law' },
        { id: 2, name: 'Corporate Law' },
        { id: 3, name: 'Family Law' },
        { id: 4, name: 'Real Estate' },
        { id: 5, name: 'Immigration' },
        { id: 6, name: 'Tax Law' },
        { id: 7, name: 'Employment Law' },
      ])
    }
  }

  const filterLawyers = () => {
    let filtered = lawyers

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(lawyer =>
        lawyer.fullName.toLowerCase().includes(term) ||
        (lawyer.specializations || []).some(s => s.toLowerCase().includes(term))
      )
    }

    if (selectedSpecializationId !== null) {
      const selectedSpec = specializations.find(s => s.id === selectedSpecializationId)?.name || ''
      const selectedSpecNormalized = selectedSpec.trim().toLowerCase()
      filtered = filtered.filter(lawyer =>
        (lawyer.specializations || []).some(s => {
          const lawyerSpecNormalized = s.trim().toLowerCase()
          return lawyerSpecNormalized === selectedSpecNormalized
            || lawyerSpecNormalized.includes(selectedSpecNormalized)
            || selectedSpecNormalized.includes(lawyerSpecNormalized)
        })
      )
    }

    setFilteredLawyers(filtered)
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-display font-bold text-gray-900 dark:text-white mb-4">
            Find Your Perfect <span className="text-primary-600 dark:text-primary-400">Legal Expert</span>
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Browse through our verified lawyers and book consultations instantly
          </p>
        </motion.div>

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-dark-800 rounded-2xl shadow-xl p-6 mb-8"
        >
          {/* Search Bar */}
          <div className="relative mb-6">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name or specialization..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-gray-50 dark:bg-dark-900 border border-gray-200 dark:border-dark-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white"
            />
          </div>

          {/* Specialization Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Specialization
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedSpecializationId(null)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  selectedSpecializationId === null
                    ? 'bg-primary-500 text-white shadow-lg'
                    : 'bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-600'
                }`}
              >
                All
              </button>
              {specializations.map(spec => (
                <button
                  key={spec.id}
                  onClick={() => setSelectedSpecializationId(spec.id)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    selectedSpecializationId === spec.id
                      ? 'bg-primary-500 text-white shadow-lg'
                      : 'bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-600'
                  }`}
                >
                  {spec.name}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Results */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading lawyers...</p>
          </div>
        ) : filteredLawyers.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">No lawyers found matching your criteria</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredLawyers.map((lawyer, index) => (
              <motion.div
                key={lawyer.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden group cursor-pointer"
                onClick={() => navigate(`/lawyer/${lawyer.id}`)}
              >
                <div className="p-6">
                  {/* Avatar and Verified Badge */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl flex items-center justify-center text-white text-2xl font-bold">
                      {lawyer.fullName?.[0] || 'L'}
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      {lawyer.isVerified && (
                        <span className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium rounded-full">
                          Verified
                        </span>
                      )}
                      {lawyer.averageRating > 0 && (
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm font-semibold text-gray-900 dark:text-white">{lawyer.averageRating.toFixed(1)}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Name and Specialization */}
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    {lawyer.fullName}
                  </h3>
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {(lawyer.specializations || []).map((spec) => (
                      <span key={`${lawyer.id}-${spec}`} className="text-xs px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded-lg font-medium">
                        {spec}
                      </span>
                    ))}
                  </div>

                  {/* Stats */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <Briefcase className="w-4 h-4" />
                      <span>{lawyer.experienceYears} years experience</span>
                    </div>
                  </div>

                  {/* Address Preview */}
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                    {lawyer.address}
                  </p>

                  {/* View Profile Button */}
                  <button className="w-full py-2.5 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-xl font-medium flex items-center justify-center gap-2 group-hover:shadow-lg transition-all">
                    View Profile
                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
