import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { User, Mail, Phone, Award, Save, Pencil, DollarSign, Plus, Trash2 } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { apiService } from '../services/api'
import type { LawyerPricingDto, InteractionTypeDto, SpecializationDto } from '../types'

export default function AccountPage() {
  const { user, updateUser } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [profilePhoto, setProfilePhoto] = useState<string | null>(user?.profilePhoto || null)
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [formData, setFormData] = useState({
    fullName: user?.fullName || '',
    email: user?.email || '',
    phone: user?.phone || '',
    city: user?.city || ''
  })
  
  // Pricing states
  const [lawyerId, setLawyerId] = useState<number | null>(null)
  const [pricings, setPricings] = useState<LawyerPricingDto[]>([])
  const [interactionTypes, setInteractionTypes] = useState<InteractionTypeDto[]>([])
  const [specializations, setSpecializations] = useState<SpecializationDto[]>([])
  const [lawyerSpecializationNames, setLawyerSpecializationNames] = useState<string[]>([])
  const [isPricingLoading, setIsPricingLoading] = useState(false)
  const [editingPricingKey, setEditingPricingKey] = useState<string | null>(null)
  const [editingPricingData, setEditingPricingData] = useState<{ price: number; durationMinutes: number }>({
    price: 0,
    durationMinutes: 60
  })
  const [newPricing, setNewPricing] = useState<Partial<LawyerPricingDto>>({
    price: 500,
    durationMinutes: 60
  })

  useEffect(() => {
    if (user?.role === 'Lawyer') {
      loadPricingData()
    }
  }, [user])

  const loadPricingData = async () => {
    setIsPricingLoading(true)
    try {
      const profile = await apiService.getMyLawyerProfile()
      setLawyerId(profile.id)
      setLawyerSpecializationNames(profile.specializations || [])
      
      const [pricingData, typesData, specsData] = await Promise.all([
        apiService.getLawyerPricing(profile.id),
        apiService.getInteractionTypes(),
        apiService.getSpecializations()
      ])
      
      setPricings(pricingData)
      setInteractionTypes(typesData)
      setSpecializations(specsData)
      
      const allowedSpecs = specsData.filter(s => (profile.specializations || []).includes(s.name))
      const specsForSelection = allowedSpecs.length > 0 ? allowedSpecs : specsData

      if (typesData.length > 0 && specsForSelection.length > 0) {
        setNewPricing(prev => ({
          ...prev,
          interactionTypeId: typesData[0].id,
          specializationId: specsForSelection[0].id
        }))
      }
    } catch (e) {
      console.error('Failed to load pricing data', e)
    } finally {
      setIsPricingLoading(false)
    }
  }

  const handleAddPricing = async () => {
    if (!lawyerId || !newPricing.interactionTypeId || !newPricing.specializationId || !newPricing.price || !newPricing.durationMinutes) return
    
    try {
      const dto: LawyerPricingDto = {
        interactionTypeId: newPricing.interactionTypeId,
        specializationId: newPricing.specializationId,
        price: newPricing.price,
        durationMinutes: newPricing.durationMinutes
      }
      await apiService.setLawyerPricing(lawyerId, dto)
      await loadPricingData()
    } catch (e) {
      alert('Failed to add pricing. It might already exist.')
    }
  }

  const allowedSpecializations = specializations.filter(s => lawyerSpecializationNames.includes(s.name))
  const selectableSpecializations = allowedSpecializations.length > 0 ? allowedSpecializations : specializations

  const handleDeletePricing = async (specId: number, intId: number) => {
    if (!lawyerId) return
    if (!confirm('Are you sure you want to delete this pricing option?')) return
    
    try {
      await apiService.deleteLawyerPricing(lawyerId, specId, intId)
      setPricings(prev => prev.filter(p => !(p.specializationId === specId && p.interactionTypeId === intId)))
    } catch (e) {
      alert('Failed to delete pricing.')
    }
  }

  const handleStartEditPricing = (pricing: LawyerPricingDto) => {
    setEditingPricingKey(`${pricing.specializationId}-${pricing.interactionTypeId}`)
    setEditingPricingData({
      price: pricing.price,
      durationMinutes: pricing.durationMinutes
    })
  }

  const handleCancelEditPricing = () => {
    setEditingPricingKey(null)
  }

  const handleSaveEditPricing = async (specializationId: number, interactionTypeId: number) => {
    if (!lawyerId) return

    try {
      await apiService.updateLawyerPricing(lawyerId, {
        specializationId,
        interactionTypeId,
        price: editingPricingData.price,
        durationMinutes: editingPricingData.durationMinutes
      })

      setPricings(prev =>
        prev.map(p =>
          p.specializationId === specializationId && p.interactionTypeId === interactionTypeId
            ? { ...p, price: editingPricingData.price, durationMinutes: editingPricingData.durationMinutes }
            : p
        )
      )
      setEditingPricingKey(null)
    } catch (e) {
      alert('Failed to update pricing.')
    }
  }

  const handleSave = () => {
    // TODO: Implement update user profile API call
    setIsEditing(false)
    alert('Profile updated successfully!')
  }

  const handlePhotoClick = () => {
    fileInputRef.current?.click()
  }

  const handlePhotoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      alert('Image size should be less than 2MB')
      return
    }

    setIsUploadingPhoto(true)

    try {
      // Convert to base64
      const reader = new FileReader()
      reader.onload = async (event) => {
        const base64 = event.target?.result as string
        
        try {
          await apiService.uploadProfilePhoto(base64)
          setProfilePhoto(base64)
          
          // Update user in context (this also updates localStorage)
          updateUser({ profilePhoto: base64 })
          
          alert('Profile photo updated successfully!')
        } catch (err) {
          console.error('Failed to upload photo:', err)
          alert('Failed to upload photo. Please try again.')
        } finally {
          setIsUploadingPhoto(false)
        }
      }
      reader.readAsDataURL(file)
    } catch (err) {
      console.error('Error reading file:', err)
      setIsUploadingPhoto(false)
    }
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-display font-bold text-gray-900 dark:text-white mb-2">
            Account Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your personal information and preferences
          </p>
        </motion.div>

        {/* Profile Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-dark-800 rounded-2xl shadow-xl p-8 mb-6"
        >
          {/* Avatar and Role */}
          <div className="flex items-center gap-6 mb-8 pb-8 border-b border-gray-200 dark:border-dark-700">
            <div className="relative">
              {profilePhoto ? (
                <img 
                  src={profilePhoto} 
                  alt={user?.fullName || 'Profile'} 
                  className="w-24 h-24 rounded-2xl object-cover"
                />
              ) : (
                <div className="w-24 h-24 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl flex items-center justify-center text-white text-3xl font-bold">
                  {user?.fullName?.[0] || 'U'}
                </div>
              )}
              <button
                onClick={handlePhotoClick}
                disabled={isUploadingPhoto}
                className="absolute -bottom-1 -right-1 w-8 h-8 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center justify-center shadow-lg transition-colors disabled:opacity-50"
                title="Edit profile photo"
              >
                {isUploadingPhoto ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Pencil className="w-4 h-4" />
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handlePhotoChange}
                className="hidden"
              />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                {user?.fullName}
              </h2>
              <p className="text-primary-600 dark:text-primary-400 font-medium mb-2">
                {user?.role}
              </p>
            </div>
          </div>

          {/* Personal Information */}
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                Personal Information
              </h3>
              <button
                onClick={() => isEditing ? handleSave() : setIsEditing(true)}
                className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl font-medium transition-colors flex items-center gap-2"
              >
                {isEditing ? (
                  <>
                    <Save className="w-4 h-4" />
                    Save Changes
                  </>
                ) : (
                  'Edit Profile'
                )}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <User className="w-4 h-4" />
                  Full Name
                </label>
                <input
                  type="text"
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  disabled={!isEditing}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-900 border border-gray-200 dark:border-dark-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white disabled:opacity-60"
                />
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Mail className="w-4 h-4" />
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={!isEditing}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-900 border border-gray-200 dark:border-dark-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white disabled:opacity-60"
                />
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Phone className="w-4 h-4" />
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  disabled={!isEditing}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-900 border border-gray-200 dark:border-dark-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white disabled:opacity-60"
                />
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <User className="w-4 h-4" />
                  City
                </label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  disabled={!isEditing}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-dark-900 border border-gray-200 dark:border-dark-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white disabled:opacity-60"
                />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Account Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-dark-800 rounded-2xl shadow-xl p-8"
        >
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Account Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-dark-900 rounded-xl">
              <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-xl flex items-center justify-center">
                <User className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Account Type</p>
                <p className="font-semibold text-gray-900 dark:text-white">{user?.role}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-dark-900 rounded-xl">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
                <Award className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Member Since</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {new Date(user?.createdAt || '').toLocaleDateString('en-US', {
                    month: 'short',
                    year: 'numeric'
                  })}
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Pricing Settings for Lawyers */}
        <AnimatePresence>
          {user?.role === 'Lawyer' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: 0.3 }}
              className="bg-white dark:bg-dark-800 rounded-2xl shadow-xl p-8 mt-6"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-primary-500" />
                  Pricing & Services
                </h3>
              </div>

              {isPricingLoading ? (
                <div className="text-center py-6 text-gray-500 dark:text-gray-400">Loading pricing configuration...</div>
              ) : (
                <div className="space-y-6">
                  {/* Active Pricings List */}
                  {pricings.length === 0 ? (
                    <div className="text-center py-6 bg-gray-50 dark:bg-dark-900 rounded-xl text-gray-500 text-sm">
                      No pricing configurations found. Add one below to accept bookings.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {pricings.map((p) => {
                        const spec = specializations.find(s => s.id === p.specializationId)
                        const interaction = interactionTypes.find(i => i.id === p.interactionTypeId)
                        const pricingKey = `${p.specializationId}-${p.interactionTypeId}`
                        const isEditingPricing = editingPricingKey === pricingKey
                        return (
                          <div key={pricingKey} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-dark-900 border border-gray-200 dark:border-dark-700 rounded-xl">
                            <div>
                              <p className="font-semibold text-gray-900 dark:text-white">{spec?.name || 'Unknown'}</p>
                              <p className="text-sm text-gray-500 dark:text-gray-400">{interaction?.name || 'Unknown'}</p>
                            </div>
                            <div className="flex items-center gap-4">
                              {isEditingPricing ? (
                                <>
                                  <input
                                    type="number"
                                    min="1"
                                    step="50"
                                    value={editingPricingData.price}
                                    onChange={(e) =>
                                      setEditingPricingData(prev => ({
                                        ...prev,
                                        price: parseFloat(e.target.value) || 0
                                      }))
                                    }
                                    className="w-24 text-sm py-1.5 px-2 bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg outline-none text-gray-900 dark:text-white"
                                  />
                                  <input
                                    type="number"
                                    min="1"
                                    step="15"
                                    value={editingPricingData.durationMinutes}
                                    onChange={(e) =>
                                      setEditingPricingData(prev => ({
                                        ...prev,
                                        durationMinutes: parseInt(e.target.value) || 0
                                      }))
                                    }
                                    className="w-20 text-sm py-1.5 px-2 bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg outline-none text-gray-900 dark:text-white"
                                    title="Duration in minutes"
                                  />
                                  <button
                                    onClick={() => handleSaveEditPricing(p.specializationId, p.interactionTypeId)}
                                    className="px-2 py-1.5 text-xs font-medium text-green-700 bg-green-100 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300 rounded-lg"
                                  >
                                    Save
                                  </button>
                                  <button
                                    onClick={handleCancelEditPricing}
                                    className="px-2 py-1.5 text-xs font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 dark:bg-dark-700 dark:text-gray-300 rounded-lg"
                                  >
                                    Cancel
                                  </button>
                                </>
                              ) : (
                                <>
                                  <span className="font-bold text-primary-600 dark:text-primary-400">{p.price} EGP • {p.durationMinutes} mins</span>
                                  <button
                                    onClick={() => handleStartEditPricing(p)}
                                    className="p-1.5 text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded-lg transition-colors"
                                    title="Edit pricing"
                                  >
                                    <Pencil className="w-4 h-4" />
                                  </button>
                                  <button onClick={() => handleDeletePricing(p.specializationId, p.interactionTypeId)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* Add New Pricing Form */}
                  <div className="p-5 border-2 border-dashed border-gray-200 dark:border-dark-700 rounded-xl">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
                      <Plus className="w-4 h-4" /> Add New Service Pricing
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
                      <div>
                        <label className="text-xs font-semibold text-gray-500 block mb-1">Specialization</label>
                        <select 
                          value={newPricing.specializationId || ''} 
                          onChange={e => setNewPricing({...newPricing, specializationId: Number(e.target.value)})}
                          className="w-full text-sm py-2 px-3 bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg outline-none text-gray-900 dark:text-white"
                        >
                          <option value="" disabled>Select specialization</option>
                          {selectableSpecializations.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-gray-500 block mb-1">Interaction Type</label>
                        <select 
                          value={newPricing.interactionTypeId || ''} 
                          onChange={e => setNewPricing({...newPricing, interactionTypeId: Number(e.target.value)})}
                          className="w-full text-sm py-2 px-3 bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg outline-none text-gray-900 dark:text-white"
                        >
                          <option value="" disabled>Select interaction</option>
                          {interactionTypes.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-gray-500 block mb-1">Price (EGP)</label>
                        <input 
                          type="number" min="0" step="50"
                          value={newPricing.price || ''}
                          onChange={e => setNewPricing({...newPricing, price: Number(e.target.value)})}
                          className="w-full text-sm py-2 px-3 bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg outline-none text-gray-900 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-gray-500 block mb-1">Duration (mins)</label>
                        <input 
                          type="number" min="15" step="15"
                          value={newPricing.durationMinutes || ''}
                          onChange={e => setNewPricing({...newPricing, durationMinutes: Number(e.target.value)})}
                          className="w-full text-sm py-2 px-3 bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg outline-none text-gray-900 dark:text-white"
                        />
                      </div>
                      <div>
                         <label className="text-xs font-semibold text-gray-500 block mb-1">Action</label>
                         <button 
                          onClick={handleAddPricing}
                          disabled={selectableSpecializations.length === 0 || interactionTypes.length === 0}
                          className="w-full h-[38px] bg-primary-500 hover:bg-primary-600 disabled:bg-gray-300 disabled:dark:bg-dark-600 text-white font-semibold rounded-lg transition-colors text-sm"
                         >
                           Add Service
                         </button>
                      </div>
                    </div>
                    {allowedSpecializations.length === 0 && specializations.length > 0 && (
                      <p className="mt-3 text-xs text-amber-600 dark:text-amber-400">
                        No mapped specialization was found for this lawyer profile. Showing all specializations as fallback.
                      </p>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
