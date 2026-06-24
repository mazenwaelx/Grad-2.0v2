import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { X, Mail, Lock, User, Loader, AlertCircle, Briefcase, Shield, Check } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import { apiService } from '../services/api'
import type { SpecializationDto } from '../types'

interface SignupModalProps {
  onClose: () => void
  onSwitchToLogin: () => void
}

export default function SignupModal({ onClose, onSwitchToLogin }: SignupModalProps) {
  const { register, isLoading, error, clearError } = useAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const [role, setRole] = useState<'User' | 'Lawyer' | 'Admin'>('User')
  
  // User fields
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [phone, setPhone] = useState('')
  const [city, setCity] = useState('')
  
  // Lawyer fields
  const [selectedSpecializations, setSelectedSpecializations] = useState<number[]>([])
  const [availableSpecializations, setAvailableSpecializations] = useState<SpecializationDto[]>([])
  const [experienceYears, setExperienceYears] = useState('')
  const [address, setAddress] = useState('')
  const [baseHourlyRate, setBaseHourlyRate] = useState('')
  
  // Admin fields
  const [adminSecret, setAdminSecret] = useState('')
  
  const [agreed, setAgreed] = useState(false)
  const [localError, setLocalError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showAdminOption, setShowAdminOption] = useState(false)
  const [adminClickCount, setAdminClickCount] = useState(0)

  // Load specializations from API when Lawyer is selected
  useEffect(() => {
    if (role === 'Lawyer') {
      loadSpecializations()
    }
  }, [role])

  const loadSpecializations = async () => {
    try {
      const data = await apiService.getSpecializations()
      setAvailableSpecializations(data)
    } catch {
      // Fallback list
      setAvailableSpecializations([
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

  const toggleSpecialization = (id: number) => {
    setSelectedSpecializations(prev =>
      prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
    )
  }

  // Hidden admin activation: click the title 5 times
  const handleTitleClick = () => {
    const newCount = adminClickCount + 1
    setAdminClickCount(newCount)
    if (newCount >= 5) {
      setShowAdminOption(true)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setLocalError('')

    if (!agreed) {
      setLocalError('Please agree to the Terms of Service and Privacy Policy')
      return
    }

    if (role === 'Lawyer') {
      if (selectedSpecializations.length === 0) {
        setLocalError('Please select at least one specialization')
        return
      }
      if (!experienceYears || !address) {
        setLocalError('Please fill in all lawyer profile fields')
        return
      }
      if (parseInt(experienceYears) < 0 || parseInt(experienceYears) > 100) {
        setLocalError('Experience years must be between 0 and 100')
        return
      }
    }

    if (role === 'Admin' && !adminSecret) {
      setLocalError('Admin secret key is required')
      return
    }

    try {
      setIsSubmitting(true)
      
      await register({
        user: {
          fullName,
          email,
          password,
          phone,
          city,
          role: role === 'Admin' ? 'Admin' : role,
          adminSecret: role === 'Admin' ? adminSecret : undefined,
        },
        lawyer: role === 'Lawyer'
          ? {
              experienceYears: parseInt(experienceYears),
              address,
              latitude: 30.0444,
              longitude: 31.2357,
              specializationIds: selectedSpecializations,
              baseHourlyRate: parseFloat(baseHourlyRate) || 0,
            }
          : undefined,
      })
      
      onClose()
      setTimeout(() => {
        if (role === 'Admin') {
          navigate('/admin')
        } else if (role === 'Lawyer') {
          navigate('/dashboard')
        } else {
          navigate('/lawyers')
        }
      }, 300)
      
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed'
      if (message.includes('409') || message.includes('Conflict') || message.includes('already')) {
        setLocalError('This email is already registered. Please use a different email or try logging in.')
      } else {
        setLocalError(message)
      }
      setIsSubmitting(false)
    }
  }

  const displayError = localError || error

  const specEmojis: Record<string, string> = {
    'Criminal Law': '⚖️', 'Corporate Law': '🏢', 'Family Law': '👨‍👩‍👧',
    'Real Estate': '🏠', 'Immigration': '✈️', 'Tax Law': '💰', 'Employment Law': '💼',
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
        className="bg-white dark:bg-dark-800 rounded-3xl p-8 max-w-md w-full shadow-2xl max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <h2
            className="text-2xl font-display font-bold text-gray-900 dark:text-white cursor-default select-none"
            onClick={handleTitleClick}
          >
            {t.auth.createAccount}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-xl transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {displayError && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-red-600 dark:text-red-400 font-medium">{displayError}</p>
                {(displayError.includes('409') || displayError.includes('already')) && (
                  <p className="text-xs text-red-500 dark:text-red-400 mt-2">
                    💡 Try{' '}
                    <button onClick={onSwitchToLogin} className="underline font-medium">logging in</button>
                    {' '}or use a different email.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Role Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t.auth.iAmA}</label>
            <div className={`grid ${showAdminOption ? 'grid-cols-3' : 'grid-cols-2'} gap-3`}>
              {(['User', 'Lawyer'] as const).map((r) => (
                <motion.label
                  key={r}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`flex items-center justify-center gap-2 p-4 border-2 rounded-2xl cursor-pointer transition-all duration-300 ${
                    role === r
                      ? 'bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-900/30 dark:to-primary-800/20 border-primary-500 shadow-lg shadow-primary-500/20'
                      : 'bg-gray-50 dark:bg-dark-700 border-gray-200 dark:border-dark-600 hover:border-primary-400'
                  }`}
                >
                  <input type="radio" name="role" value={r} checked={role === r} onChange={() => setRole(r)} className="sr-only" />
                  {r === 'User' ? <User className={`w-5 h-5 ${role === r ? 'text-primary-600' : ''}`} /> : <Briefcase className={`w-5 h-5 ${role === r ? 'text-primary-600' : ''}`} />}
                  <span className="font-medium text-gray-900 dark:text-white">{r === 'User' ? t.auth.client : t.auth.lawyer}</span>
                </motion.label>
              ))}
              {showAdminOption && (
                <motion.label
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`flex items-center justify-center gap-2 p-4 border-2 rounded-2xl cursor-pointer transition-all duration-300 ${
                    role === 'Admin'
                      ? 'bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/20 border-red-500 shadow-lg shadow-red-500/20'
                      : 'bg-gray-50 dark:bg-dark-700 border-gray-200 dark:border-dark-600 hover:border-red-400'
                  }`}
                >
                  <input type="radio" name="role" value="Admin" checked={role === 'Admin'} onChange={() => setRole('Admin')} className="sr-only" />
                  <Shield className={`w-5 h-5 ${role === 'Admin' ? 'text-red-600' : ''}`} />
                  <span className="font-medium text-gray-900 dark:text-white">Admin</span>
                </motion.label>
              )}
            </div>
          </div>

          {/* Basic Fields */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t.auth.fullName}</label>
            <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="John Doe" required disabled={isLoading || isSubmitting}
              className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all disabled:opacity-50 text-gray-900 dark:text-white" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t.auth.email}</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.com" required disabled={isLoading || isSubmitting}
                className="w-full pl-12 pr-4 py-3 bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all disabled:opacity-50 text-gray-900 dark:text-white" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t.auth.phoneNumber}</label>
              <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+20 123456789" required disabled={isLoading || isSubmitting}
                className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all disabled:opacity-50 text-gray-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t.auth.city}</label>
              <input type="text" value={city} onChange={(e) => setCity(e.target.value)} placeholder="Cairo" required disabled={isLoading || isSubmitting}
                className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all disabled:opacity-50 text-gray-900 dark:text-white" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{t.auth.password}</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required disabled={isLoading || isSubmitting} minLength={6}
                className="w-full pl-12 pr-4 py-3 bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all disabled:opacity-50 text-gray-900 dark:text-white" />
            </div>
          </div>

          {/* Admin Secret */}
          {role === 'Admin' && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-3 pt-4 border-t border-red-200 dark:border-red-900">
              <p className="text-sm font-medium text-red-600 dark:text-red-400 flex items-center gap-2">
                <Shield className="w-4 h-4" /> Admin Registration
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Admin Secret Key</label>
                <input type="password" value={adminSecret} onChange={(e) => setAdminSecret(e.target.value)} placeholder="Enter admin secret..." required disabled={isLoading || isSubmitting}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-700 border border-red-200 dark:border-red-800 rounded-2xl focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition-all disabled:opacity-50 text-gray-900 dark:text-white" />
              </div>
            </motion.div>
          )}

          {/* Lawyer Fields — Checklist Specializations */}
          {role === 'Lawyer' && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              transition={{ duration: 0.3 }}
              className="space-y-4 pt-4 border-t border-gray-200 dark:border-dark-700"
            >
              <p className="text-sm font-medium text-primary-600 dark:text-primary-400 flex items-center gap-2">
                <Briefcase className="w-4 h-4" /> Lawyer Profile Information
              </p>

              {/* Specialization Checklist */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Specializations (select one or more)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {availableSpecializations.map((spec) => (
                    <motion.button
                      key={spec.id}
                      type="button"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => toggleSpecialization(spec.id)}
                      disabled={isLoading || isSubmitting}
                      className={`flex items-center gap-2 p-3 border-2 rounded-xl text-left text-sm font-medium transition-all ${
                        selectedSpecializations.includes(spec.id)
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                          : 'border-gray-200 dark:border-dark-600 bg-gray-50 dark:bg-dark-700 text-gray-700 dark:text-gray-300 hover:border-primary-300'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                        selectedSpecializations.includes(spec.id)
                          ? 'border-primary-500 bg-primary-500'
                          : 'border-gray-300 dark:border-dark-500'
                      }`}>
                        {selectedSpecializations.includes(spec.id) && (
                          <Check className="w-3 h-3 text-white" />
                        )}
                      </div>
                      <span>{specEmojis[spec.name] || '📋'} {spec.name}</span>
                    </motion.button>
                  ))}
                </div>
                {selectedSpecializations.length > 0 && (
                  <p className="text-xs text-primary-600 dark:text-primary-400 mt-2">
                    {selectedSpecializations.length} specialization{selectedSpecializations.length > 1 ? 's' : ''} selected
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Years of Experience</label>
                <input type="number" value={experienceYears} onChange={(e) => setExperienceYears(e.target.value)} placeholder="10" required={role === 'Lawyer'} min="0" max="60" disabled={isLoading || isSubmitting}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all disabled:opacity-50 text-gray-900 dark:text-white" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Office Address</label>
                <textarea value={address} onChange={(e) => setAddress(e.target.value)} placeholder="123 Main Street, Cairo, Egypt" required={role === 'Lawyer'} rows={3} disabled={isLoading || isSubmitting}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all resize-none disabled:opacity-50 text-gray-900 dark:text-white" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Base Hourly Rate (Optional)</label>
                <div className="relative">
                  <input 
                    type="number" 
                    value={baseHourlyRate} 
                    onChange={(e) => setBaseHourlyRate(e.target.value)} 
                    placeholder="500" 
                    min="0" 
                    step="50" 
                    disabled={isLoading || isSubmitting}
                    className="w-full pl-4 pr-16 py-3 bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-2xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all disabled:opacity-50 text-gray-900 dark:text-white" 
                  />
                  <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                    <span className="text-gray-500 dark:text-gray-400 font-medium">EGP</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Leave empty to set later</p>
              </div>
            </motion.div>
          )}

          <label className="flex items-start gap-2">
            <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} className="mt-1 rounded" />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {t.auth.agreeToTerms}{' '}
              <a href="/terms-of-service" target="_blank" rel="noopener noreferrer" className="text-primary-600 dark:text-primary-400 hover:underline">{t.auth.termsOfService}</a>{' '}
              {t.auth.and}{' '}
              <a href="/privacy-policy" target="_blank" rel="noopener noreferrer" className="text-primary-600 dark:text-primary-400 hover:underline">{t.auth.privacyPolicy}</a>
            </span>
          </label>

          <motion.button
            type="submit"
            disabled={isLoading || isSubmitting}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={`w-full py-3 ${
              role === 'Admin'
                ? 'bg-gradient-to-r from-red-500 to-red-700'
                : 'bg-gradient-to-r from-primary-500 to-primary-700'
            } text-white rounded-2xl font-semibold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
          >
            {isLoading || isSubmitting ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                {t.auth.creatingAccount}
              </>
            ) : (
              t.auth.createAccount
            )}
          </motion.button>
        </form>

        <p className="text-center text-sm text-gray-600 dark:text-gray-400 mt-6">
          {t.auth.alreadyHaveAccount}{' '}
          <button onClick={onSwitchToLogin} className="text-primary-600 dark:text-primary-400 font-medium hover:underline">
            {t.auth.signIn}
          </button>
        </p>
      </motion.div>
    </motion.div>
  )
}
