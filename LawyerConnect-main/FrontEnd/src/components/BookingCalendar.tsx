import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Calendar, Clock, Check } from 'lucide-react'
import { apiService } from '../services/api'
import type { InteractionTypeDto, LawyerPricingDto, SpecializationDto } from '../types'

interface BookingCalendarProps {
  lawyerId: number
  onSuccess: () => void
  onCancel: () => void
}

export default function BookingCalendar({ lawyerId, onSuccess, onCancel }: BookingCalendarProps) {
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [selectedTime, setSelectedTime] = useState<string>('')
  const [selectedPricingKey, setSelectedPricingKey] = useState<string>('')
  const [pricings, setPricings] = useState<LawyerPricingDto[]>([])
  const [interactionTypes, setInteractionTypes] = useState<InteractionTypeDto[]>([])
  const [specializations, setSpecializations] = useState<SpecializationDto[]>([])
  const [isPricingLoading, setIsPricingLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const loadPricingOptions = async () => {
      setIsPricingLoading(true)
      try {
        // Only fetch pricing - specializations and interaction types are cached globally
        const pricingData = await apiService.getLawyerPricing(lawyerId)
        setPricings(pricingData)

        // Load types and specs from cache or API (will be cached by api service)
        const [typesData, specsData] = await Promise.all([
          apiService.getInteractionTypes(),
          apiService.getSpecializations()
        ])

        setInteractionTypes(typesData)
        setSpecializations(specsData)

        if (pricingData.length > 0) {
          setSelectedPricingKey(`${pricingData[0].specializationId}-${pricingData[0].interactionTypeId}`)
        }
      } catch (err) {
        setError(`Failed to load pricing options for this lawyer: ${err instanceof Error ? err.message : 'Unknown error'}`)
      } finally {
        setIsPricingLoading(false)
      }
    }

    loadPricingOptions()
  }, [lawyerId])

  const today = new Date()
  const dates = Array.from({ length: 14 }, (_, i) => {
    const date = new Date(today)
    date.setDate(date.getDate() + i + 1)
    return date
  })

  const timeSlots = [
    '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'
  ]

  const handleSubmit = async () => {
    if (!selectedDate || !selectedTime || !selectedPricingKey) {
      setError('Please select service, date, and time')
      return
    }

    try {
      setIsSubmitting(true)
      setError('')
      
      const dateTime = `${selectedDate}T${selectedTime}:00`
      const [specializationIdRaw, interactionTypeIdRaw] = selectedPricingKey.split('-')
      const specializationId = Number(specializationIdRaw)
      const interactionTypeId = Number(interactionTypeIdRaw)

      await apiService.createBooking({
        lawyerId,
        specializationId,
        interactionTypeId,
        date: dateTime
      })
      
      // Clear booking caches after successful booking
      sessionStorage.removeItem('user_bookings_cache')
      sessionStorage.removeItem('user_bookings_cache_timestamp')
      sessionStorage.removeItem('lawyer_bookings_cache')
      sessionStorage.removeItem('lawyer_bookings_cache_timestamp')
      
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create booking')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Service Selection */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Select Service
        </label>
        {isPricingLoading ? (
          <div className="p-3 bg-gray-100 dark:bg-dark-900 rounded-xl text-sm text-gray-500 dark:text-gray-400">
            Loading service options...
          </div>
        ) : pricings.length === 0 ? (
          <div className="p-3 bg-yellow-100 dark:bg-yellow-900/20 rounded-xl text-sm text-yellow-800 dark:text-yellow-300">
            This lawyer has no pricing configured yet. Booking is unavailable.
          </div>
        ) : (
          <div className="space-y-2 max-h-44 overflow-y-auto">
            {pricings.map((pricing) => {
              const key = `${pricing.specializationId}-${pricing.interactionTypeId}`
              const spec = specializations.find(s => s.id === pricing.specializationId)
              const interaction = interactionTypes.find(i => i.id === pricing.interactionTypeId)
              const isSelected = selectedPricingKey === key
              return (
                <button
                  key={key}
                  onClick={() => setSelectedPricingKey(key)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    isSelected
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-dark-700 bg-gray-50 dark:bg-dark-900 hover:bg-gray-100 dark:hover:bg-dark-800'
                  }`}
                >
                  <p className="font-semibold text-gray-900 dark:text-white">{spec?.name || 'Service'}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {interaction?.name || 'Consultation'} • {pricing.durationMinutes} mins • {pricing.price} EGP
                  </p>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Date Selection */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          <Calendar className="w-4 h-4" />
          Select Date
        </label>
        <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
          {dates.map((date) => {
            const dateStr = date.toISOString().split('T')[0]
            const isSelected = selectedDate === dateStr
            return (
              <button
                key={dateStr}
                onClick={() => setSelectedDate(dateStr)}
                className={`p-3 rounded-xl text-sm font-medium transition-all ${
                  isSelected
                    ? 'bg-primary-500 text-white shadow-lg'
                    : 'bg-gray-100 dark:bg-dark-900 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-700'
                }`}
              >
                <div className="text-xs opacity-75">
                  {date.toLocaleDateString('en-US', { weekday: 'short' })}
                </div>
                <div className="font-bold">
                  {date.getDate()}
                </div>
                <div className="text-xs opacity-75">
                  {date.toLocaleDateString('en-US', { month: 'short' })}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Time Selection */}
      {selectedDate && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            <Clock className="w-4 h-4" />
            Select Time
          </label>
          <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
            {timeSlots.map((time) => {
              const isSelected = selectedTime === time
              return (
                <button
                  key={time}
                  onClick={() => setSelectedTime(time)}
                  className={`p-3 rounded-xl text-sm font-medium transition-all ${
                    isSelected
                      ? 'bg-primary-500 text-white shadow-lg'
                      : 'bg-gray-100 dark:bg-dark-900 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-700'
                  }`}
                >
                  {time}
                </button>
              )
            })}
          </div>
        </motion.div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Selected Summary */}
      {selectedDate && selectedTime && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-primary-50 dark:bg-primary-900/20 rounded-xl"
        >
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Selected:</p>
          <p className="font-semibold text-gray-900 dark:text-white">
            {new Date(selectedDate).toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })} at {selectedTime}
          </p>
        </motion.div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onCancel}
          className="flex-1 py-3 border border-gray-300 dark:border-dark-700 text-gray-700 dark:text-gray-300 rounded-xl font-medium hover:bg-gray-50 dark:hover:bg-dark-900 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={!selectedDate || !selectedTime || !selectedPricingKey || isSubmitting || pricings.length === 0}
          className="flex-1 py-3 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Booking...
            </>
          ) : (
            <>
              <Check className="w-5 h-5" />
              Confirm Booking
            </>
          )}
        </button>
      </div>
    </div>
  )
}
