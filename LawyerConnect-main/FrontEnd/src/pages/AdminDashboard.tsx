import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Users, Briefcase, Calendar, CreditCard, CheckCircle, XCircle, Shield, UserX, UserCheck, Loader } from 'lucide-react'
import { apiService } from '../services/api'
import type { UserResponseDto, LawyerResponseDto, BookingResponseDto, PaymentSessionResponseDto } from '../types'

type Tab = 'users' | 'lawyers' | 'bookings' | 'payments'

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('lawyers')
  const [users, setUsers] = useState<UserResponseDto[]>([])
  const [pendingLawyers, setPendingLawyers] = useState<LawyerResponseDto[]>([])
  const [bookings, setBookings] = useState<BookingResponseDto[]>([])
  const [payments, setPayments] = useState<PaymentSessionResponseDto[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [rejectReason, setRejectReason] = useState('')
  const [rejectingId, setRejectingId] = useState<number | null>(null)

  useEffect(() => {
    loadTabData(activeTab)
  }, [activeTab])

  const loadTabData = async (tab: Tab) => {
    setIsLoading(true)
    try {
      switch (tab) {
        case 'users':
          setUsers(await apiService.adminGetAllUsers())
          break
        case 'lawyers':
          setPendingLawyers(await apiService.adminGetPendingLawyers())
          break
        case 'bookings':
          setBookings(await apiService.adminGetAllBookings())
          break
        case 'payments':
          setPayments(await apiService.adminGetAllPayments())
          break
      }
    } catch (error) {
      console.error(`Failed to load ${tab}:`, error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerify = async (id: number) => {
    try {
      await apiService.adminVerifyLawyer(id)
      await loadTabData('lawyers')
    } catch (error) {
      console.error('Failed to verify lawyer:', error)
    }
  }

  const handleReject = async (id: number) => {
    if (!rejectReason.trim()) return
    try {
      await apiService.adminRejectLawyer(id, rejectReason)
      setRejectingId(null)
      setRejectReason('')
      await loadTabData('lawyers')
    } catch (error) {
      console.error('Failed to reject lawyer:', error)
    }
  }

  const handleSuspend = async (id: number) => {
    if (!confirm('Are you sure you want to suspend this user?')) return
    try {
      await apiService.adminSuspendUser(id)
      await loadTabData('users')
    } catch (error) {
      console.error('Failed to suspend user:', error)
    }
  }

  const handleUnsuspend = async (id: number) => {
    try {
      await apiService.adminUnsuspendUser(id)
      await loadTabData('users')
    } catch (error) {
      console.error('Failed to unsuspend user:', error)
    }
  }

  const tabs = [
    { id: 'lawyers' as Tab, label: 'Pending Lawyers', icon: Briefcase, count: pendingLawyers.length },
    { id: 'users' as Tab, label: 'Users', icon: Users },
    { id: 'bookings' as Tab, label: 'Bookings', icon: Calendar },
    { id: 'payments' as Tab, label: 'Payments', icon: CreditCard },
  ]

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed': case 'paid': case 'completed': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
      case 'pending': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
      case 'cancelled': case 'failed': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
      default: return 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400'
    }
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-red-700 rounded-2xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-display font-bold text-gray-900 dark:text-white">Admin Dashboard</h1>
              <p className="text-gray-600 dark:text-gray-400">Manage platform users, lawyers, bookings, and payments</p>
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex flex-wrap gap-3 mb-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-primary-500 text-white shadow-lg'
                  : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span className="ml-1 px-2 py-0.5 text-xs rounded-full bg-white/20">{tab.count}</span>
              )}
            </button>
          ))}
        </motion.div>

        {/* Content */}
        {isLoading ? (
          <div className="text-center py-12">
            <Loader className="w-12 h-12 text-primary-500 animate-spin mx-auto" />
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
          </div>
        ) : (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            {/* ========== PENDING LAWYERS ========== */}
            {activeTab === 'lawyers' && (
              <div className="space-y-4">
                {pendingLawyers.length === 0 ? (
                  <div className="text-center py-12 bg-white dark:bg-dark-800 rounded-2xl">
                    <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">No pending lawyers to review</p>
                  </div>
                ) : (
                  pendingLawyers.map((lawyer) => (
                    <div key={lawyer.id} className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg p-6">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="flex items-start gap-4">
                          <div className="w-14 h-14 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center text-white font-bold text-xl">
                            {lawyer.fullName?.[0] || 'L'}
                          </div>
                          <div>
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white">{lawyer.fullName}</h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400">{lawyer.email}</p>
                            <div className="flex flex-wrap gap-2 mt-2">
                              {lawyer.specializations?.map((s, i) => (
                                <span key={i} className="px-2 py-1 text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded-lg">
                                  {s}
                                </span>
                              ))}
                            </div>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                              {lawyer.experienceYears} years experience • {lawyer.address}
                            </p>
                          </div>
                        </div>
                        <div className="flex flex-col gap-2">
                          <button
                            onClick={() => handleVerify(lawyer.id)}
                            className="px-5 py-2 bg-green-500 hover:bg-green-600 text-white rounded-xl font-medium transition-colors flex items-center gap-2"
                          >
                            <CheckCircle className="w-4 h-4" /> Approve
                          </button>
                          {rejectingId === lawyer.id ? (
                            <div className="space-y-2">
                              <input
                                type="text"
                                value={rejectReason}
                                onChange={(e) => setRejectReason(e.target.value)}
                                placeholder="Rejection reason..."
                                className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-xl outline-none focus:ring-2 focus:ring-red-500 text-gray-900 dark:text-white"
                              />
                              <div className="flex gap-2">
                                <button onClick={() => handleReject(lawyer.id)} className="flex-1 px-3 py-1.5 bg-red-500 text-white text-sm rounded-lg">Confirm</button>
                                <button onClick={() => setRejectingId(null)} className="flex-1 px-3 py-1.5 bg-gray-200 dark:bg-dark-600 text-gray-700 dark:text-gray-300 text-sm rounded-lg">Cancel</button>
                              </div>
                            </div>
                          ) : (
                            <button
                              onClick={() => setRejectingId(lawyer.id)}
                              className="px-5 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl font-medium transition-colors flex items-center gap-2"
                            >
                              <XCircle className="w-4 h-4" /> Reject
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* ========== ALL USERS ========== */}
            {activeTab === 'users' && (
              <div className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-dark-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">User</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Role</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">City</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Joined</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-dark-700">
                      {users.map((u) => (
                        <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-dark-700/50 transition-colors">
                          <td className="px-6 py-4">
                            <div>
                              <p className="font-medium text-gray-900 dark:text-white">{u.fullName}</p>
                              <p className="text-sm text-gray-500 dark:text-gray-400">{u.email}</p>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                              u.role === 'Admin' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                              u.role === 'Lawyer' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' :
                              'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400'
                            }`}>{u.role}</span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{u.city}</td>
                          <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                            {new Date(u.createdAt).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4">
                            {u.role !== 'Admin' && (
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleSuspend(u.id)}
                                  className="px-3 py-1.5 text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors flex items-center gap-1"
                                >
                                  <UserX className="w-3 h-3" /> Suspend
                                </button>
                                <button
                                  onClick={() => handleUnsuspend(u.id)}
                                  className="px-3 py-1.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-lg hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors flex items-center gap-1"
                                >
                                  <UserCheck className="w-3 h-3" /> Unsuspend
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {users.length === 0 && (
                  <div className="text-center py-12 text-gray-400">No users found</div>
                )}
              </div>
            )}

            {/* ========== ALL BOOKINGS ========== */}
            {activeTab === 'bookings' && (
              <div className="space-y-4">
                {bookings.length === 0 ? (
                  <div className="text-center py-12 bg-white dark:bg-dark-800 rounded-2xl">
                    <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">No bookings found</p>
                  </div>
                ) : (
                  bookings.map((booking) => (
                    <div key={booking.id} className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg p-5">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {booking.clientName || 'Client'} → {booking.lawyerName || 'Lawyer'}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {new Date(booking.date).toLocaleDateString()} at {new Date(booking.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(booking.status)}`}>
                            {booking.status}
                          </span>
                          <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(booking.paymentStatus)}`}>
                            {booking.paymentStatus}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* ========== ALL PAYMENTS ========== */}
            {activeTab === 'payments' && (
              <div className="bg-white dark:bg-dark-800 rounded-2xl shadow-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-dark-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">ID</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Booking</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Amount</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-dark-700">
                      {payments.map((p) => (
                        <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-dark-700/50 transition-colors">
                          <td className="px-6 py-4 text-sm text-gray-900 dark:text-white font-medium">#{p.id}</td>
                          <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">Booking #{p.bookingId}</td>
                          <td className="px-6 py-4 text-sm font-semibold text-gray-900 dark:text-white">{p.amount} EGP</td>
                          <td className="px-6 py-4">
                            <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(p.status)}`}>
                              {p.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                            {new Date(p.createdAt).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {payments.length === 0 && (
                  <div className="text-center py-12 text-gray-400">No payments found</div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  )
}
