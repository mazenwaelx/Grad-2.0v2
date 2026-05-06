import { useState } from 'react'
import { motion } from 'framer-motion'
import { X, CreditCard, CheckCircle, Shield, Lock } from 'lucide-react'
import { apiService } from '../services/api'

interface PaymentModalProps {
  bookingId: number
  amount: number
  lawyerName: string
  onClose: () => void
  onSuccess: () => void
}

export default function PaymentModal({ bookingId, amount, lawyerName, onClose, onSuccess }: PaymentModalProps) {
  const [step, setStep] = useState<'details' | 'processing' | 'success' | 'error'>('details')
  const [error, setError] = useState('')

  const handlePay = async () => {
    try {
      setStep('processing')
      setError('')

      // Step 1: Create payment session
      const session = await apiService.createPaymentSession({
        bookingId,
        amount,
      })

      // Step 2: Simulate payment delay
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Step 3: Confirm payment
      await apiService.confirmPayment(session.id)

      setStep('success')
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 2000)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Payment failed'
      setError(message)
      setStep('error')
    }
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
        className="bg-white dark:bg-dark-800 rounded-3xl p-8 max-w-md w-full shadow-2xl"
      >
        {step === 'success' ? (
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="text-center py-8">
            <div className="w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-10 h-10 text-green-500" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Payment Successful!</h3>
            <p className="text-gray-600 dark:text-gray-400">Your booking has been confirmed</p>
          </motion.div>
        ) : step === 'processing' ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 relative">
              <div className="absolute inset-0 border-4 border-primary-200 dark:border-primary-900 rounded-full" />
              <div className="absolute inset-0 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Processing Payment</h3>
            <p className="text-gray-600 dark:text-gray-400">Please wait while we process your payment...</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-display font-bold text-gray-900 dark:text-white">
                Payment
              </h2>
              <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-xl transition-colors">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-600 dark:text-red-400">
                {error}
              </div>
            )}

            {/* Order Summary */}
            <div className="bg-gray-50 dark:bg-dark-700 rounded-2xl p-5 mb-6">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Order Summary</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-gray-900 dark:text-white">
                  <span>Consultation with {lawyerName}</span>
                </div>
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>Booking #{bookingId}</span>
                </div>
                <div className="border-t border-gray-200 dark:border-dark-600 pt-2 mt-2">
                  <div className="flex justify-between text-lg font-bold text-gray-900 dark:text-white">
                    <span>Total</span>
                    <span>{amount} EGP</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Payment Method */}
            <div className="mb-6">
              <div className="flex items-center gap-3 p-4 border-2 border-primary-500 bg-primary-50 dark:bg-primary-900/20 rounded-2xl">
                <CreditCard className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Simulated Payment</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Click to confirm payment</p>
                </div>
              </div>
            </div>

            {/* Security Badges */}
            <div className="flex items-center justify-center gap-4 mb-6 text-xs text-gray-400">
              <div className="flex items-center gap-1">
                <Shield className="w-3.5 h-3.5" />
                <span>Secure</span>
              </div>
              <div className="flex items-center gap-1">
                <Lock className="w-3.5 h-3.5" />
                <span>Encrypted</span>
              </div>
            </div>

            <motion.button
              onClick={handlePay}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-3.5 bg-gradient-to-r from-green-500 to-green-700 text-white rounded-2xl font-semibold shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
            >
              <CreditCard className="w-5 h-5" />
              Pay {amount} EGP
            </motion.button>
          </>
        )}
      </motion.div>
    </motion.div>
  )
}
