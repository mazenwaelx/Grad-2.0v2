import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useNavigate, useLocation } from 'react-router-dom'
import { Moon, Sun, Menu, X, Scale, Bot, LogOut, Home, Users, Calendar, Settings, Languages, Bell, Shield, Check } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import { apiService } from '../services/api'
import type { NotificationResponseDto } from '../types'

interface NavbarProps {
  isDark: boolean
  toggleTheme: () => void
  onLoginClick: () => void
  onSignupClick: () => void
  onAIChatClick: () => void
}

export default function Navbar({ isDark, toggleTheme, onLoginClick, onSignupClick, onAIChatClick }: NavbarProps) {
  const { user, isLoggedIn, logout } = useAuth()
  const { language, setLanguage, t } = useLanguage()
  const navigate = useNavigate()
  const location = useLocation()
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState<NotificationResponseDto[]>([])
  const notifRef = useRef<HTMLDivElement>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'ar' : 'en')
  }

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Poll notifications when logged in
  useEffect(() => {
    if (isLoggedIn) {
      fetchUnreadCount()
      pollRef.current = setInterval(fetchUnreadCount, 30000)
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [isLoggedIn])

  // Close notification dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const fetchUnreadCount = async () => {
    try {
      const data = await apiService.getUnreadCount()
      setUnreadCount(data.unreadCount)
    } catch {
      // silently fail
    }
  }

  const loadNotifications = async () => {
    try {
      const data = await apiService.getNotifications(1, 10)
      setNotifications(data)
    } catch {
      // silently fail
    }
  }

  const handleBellClick = async () => {
    if (!showNotifications) {
      await loadNotifications()
    }
    setShowNotifications(!showNotifications)
  }

  const handleMarkRead = async (id: number) => {
    try {
      await apiService.markNotificationRead(id)
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, isRead: true } : n))
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch {
      // silently fail
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await apiService.markAllNotificationsRead()
      setNotifications(prev => prev.map(n => ({ ...n, isRead: true })))
      setUnreadCount(0)
    } catch {
      // silently fail
    }
  }

  const handleLogout = () => {
    logout()
    setShowUserMenu(false)
    navigate('/')
  }

  const formatTimeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return `${Math.floor(hrs / 24)}d ago`
  }

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-white/80 dark:bg-dark-900/80 backdrop-blur-xl shadow-lg'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <motion.button
            onClick={() => navigate('/')}
            className="flex items-center gap-3"
            whileHover={{ scale: 1.05 }}
          >
            <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl flex items-center justify-center shadow-lg">
              <Scale className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-display font-bold bg-gradient-to-r from-primary-600 to-primary-800 dark:from-primary-400 dark:to-primary-600 bg-clip-text text-transparent">
              Estasheer
            </span>
          </motion.button>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <button onClick={() => navigate('/')} className={`flex items-center gap-2 transition-colors font-medium ${location.pathname === '/' ? 'text-primary-600 dark:text-primary-400' : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400'}`}>
              <Home className="w-4 h-4" /> {t.nav.home}
            </button>
            <button onClick={() => navigate('/lawyers')} className={`flex items-center gap-2 transition-colors font-medium ${location.pathname === '/lawyers' ? 'text-primary-600 dark:text-primary-400' : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400'}`}>
              <Users className="w-4 h-4" /> {t.nav.browseLawyers}
            </button>
            {isLoggedIn && (
              <button onClick={() => navigate('/dashboard')} className={`flex items-center gap-2 transition-colors font-medium ${location.pathname === '/dashboard' ? 'text-primary-600 dark:text-primary-400' : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400'}`}>
                <Calendar className="w-4 h-4" /> {t.nav.myAppointments}
              </button>
            )}
            {isLoggedIn && user?.role === 'Admin' && (
              <button onClick={() => navigate('/admin')} className={`flex items-center gap-2 transition-colors font-medium ${location.pathname === '/admin' ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400'}`}>
                <Shield className="w-4 h-4" /> Admin
              </button>
            )}
          </div>

          {/* Actions */}
          <div className="hidden md:flex items-center gap-3">
            {/* AI Chat */}
            <motion.button onClick={onAIChatClick} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-500 to-purple-700 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all">
              <Bot className="w-5 h-5" /> <span>{t.nav.aiAssistant}</span>
            </motion.button>

            {/* Language */}
            <motion.button onClick={toggleLanguage} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 px-3 py-2.5 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl font-medium shadow-md hover:shadow-lg transition-all">
              <Languages className="w-4 h-4" /> <span className="text-sm font-semibold">{language === 'en' ? 'AR' : 'EN'}</span>
            </motion.button>

            {/* Theme */}
            <button onClick={toggleTheme} className="p-2.5 rounded-xl hover:bg-gray-100 dark:hover:bg-dark-800 transition-colors">
              {isDark ? <Sun className="w-5 h-5 text-primary-500" /> : <Moon className="w-5 h-5 text-gray-700" />}
            </button>

            {/* Notification Bell */}
            {isLoggedIn && (
              <div ref={notifRef} className="relative">
                <button onClick={handleBellClick} className="relative p-2.5 rounded-xl hover:bg-gray-100 dark:hover:bg-dark-800 transition-colors">
                  <Bell className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>

                {showNotifications && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    className="absolute right-0 mt-2 w-80 bg-white dark:bg-dark-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-dark-700 overflow-hidden z-50"
                  >
                    <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-dark-700">
                      <h3 className="font-bold text-gray-900 dark:text-white">Notifications</h3>
                      {unreadCount > 0 && (
                        <button onClick={handleMarkAllRead} className="text-xs text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1">
                          <Check className="w-3 h-3" /> Mark all read
                        </button>
                      )}
                    </div>
                    <div className="max-h-80 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="p-6 text-center text-gray-400">
                          <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">No notifications</p>
                        </div>
                      ) : (
                        notifications.map((notif) => (
                          <div
                            key={notif.id}
                            onClick={() => !notif.isRead && handleMarkRead(notif.id)}
                            className={`p-4 border-b border-gray-100 dark:border-dark-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-700/50 transition-colors ${
                              !notif.isRead ? 'bg-primary-50/50 dark:bg-primary-900/10' : ''
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              {!notif.isRead && (
                                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 flex-shrink-0" />
                              )}
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{notif.title}</p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{notif.message}</p>
                                <p className="text-[10px] text-gray-400 mt-1">{formatTimeAgo(notif.createdAt)}</p>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </motion.div>
                )}
              </div>
            )}

            {/* User Menu */}
            {isLoggedIn ? (
              <div 
                className="relative"
                onMouseEnter={() => setShowUserMenu(true)}
                onMouseLeave={() => setShowUserMenu(false)}
              >
                <button
                  className="flex items-center gap-2 px-4 py-2.5 bg-gray-100 dark:bg-dark-800 rounded-xl hover:bg-gray-200 dark:hover:bg-dark-700 transition-colors"
                >
                  {user?.profilePhoto ? (
                    <img src={user.profilePhoto} alt={user.fullName || 'Profile'} className="w-8 h-8 rounded-lg object-cover" />
                  ) : (
                    <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                      <span className="text-white font-semibold text-sm">{user?.fullName?.[0] || 'U'}</span>
                    </div>
                  )}
                  <span className="font-medium text-gray-900 dark:text-white">{user?.fullName?.split(' ')[0] || 'User'}</span>
                </button>

                {showUserMenu && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }} 
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute right-0 top-full pt-2 w-48 z-50"
                  >
                    <div className="bg-white dark:bg-dark-800 rounded-xl shadow-xl border border-gray-200 dark:border-dark-700 py-2">
                      <div className="px-4 py-2 border-b border-gray-200 dark:border-dark-700">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.fullName}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</p>
                        <p className="text-xs text-primary-600 dark:text-primary-400 mt-1">{user?.role}</p>
                      </div>
                      <button onClick={() => { navigate('/dashboard'); setShowUserMenu(false) }}
                        className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 transition-colors flex items-center gap-2">
                        <Calendar className="w-4 h-4" /> {t.nav.myAppointments}
                      </button>
                      <button onClick={() => { navigate('/account'); setShowUserMenu(false) }}
                        className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 transition-colors flex items-center gap-2">
                        <Settings className="w-4 h-4" /> {t.nav.accountSettings}
                      </button>
                      {user?.role === 'Admin' && (
                        <button onClick={() => { navigate('/admin'); setShowUserMenu(false) }}
                          className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors flex items-center gap-2">
                          <Shield className="w-4 h-4" /> Admin Dashboard
                        </button>
                      )}
                      <button onClick={handleLogout}
                        className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors flex items-center gap-2">
                        <LogOut className="w-4 h-4" /> {t.nav.logout}
                      </button>
                    </div>
                  </motion.div>
                )}
              </div>
            ) : (
              <>
                <button onClick={onLoginClick} className="px-6 py-2.5 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors font-medium">
                  {t.nav.login}
                </button>
                <motion.button onClick={onSignupClick} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                  className="px-6 py-2.5 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-xl font-medium shadow-lg shadow-primary-500/30 hover:shadow-xl transition-all">
                  {t.nav.getStarted}
                </motion.button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="md:hidden p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-dark-800 transition-colors">
            {isMobileMenuOpen ? <X className="w-6 h-6 text-gray-700 dark:text-gray-300" /> : <Menu className="w-6 h-6 text-gray-700 dark:text-gray-300" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
          className="md:hidden bg-white dark:bg-dark-900 border-t border-gray-200 dark:border-dark-800">
          <div className="px-4 py-6 space-y-4">
            <button onClick={onAIChatClick} className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-500 to-purple-700 text-white rounded-xl font-medium">
              <Bot className="w-5 h-5" /> {t.nav.aiAssistant}
            </button>
            <button onClick={toggleLanguage} className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl font-medium">
              <Languages className="w-5 h-5" /> <span>{language === 'en' ? 'العربية' : 'English'}</span>
            </button>
            <button onClick={() => { navigate('/'); setIsMobileMenuOpen(false) }} className="w-full text-left flex items-center gap-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 font-medium">
              <Home className="w-4 h-4" /> {t.nav.home}
            </button>
            <button onClick={() => { navigate('/lawyers'); setIsMobileMenuOpen(false) }} className="w-full text-left flex items-center gap-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 font-medium">
              <Users className="w-4 h-4" /> {t.nav.browseLawyers}
            </button>
            {isLoggedIn && (
              <button onClick={() => { navigate('/dashboard'); setIsMobileMenuOpen(false) }} className="w-full text-left flex items-center gap-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 font-medium">
                <Calendar className="w-4 h-4" /> {t.nav.myAppointments}
              </button>
            )}
            {isLoggedIn && user?.role === 'Admin' && (
              <button onClick={() => { navigate('/admin'); setIsMobileMenuOpen(false) }} className="w-full text-left flex items-center gap-2 text-red-600 dark:text-red-400 font-medium">
                <Shield className="w-4 h-4" /> Admin Dashboard
              </button>
            )}
            {isLoggedIn ? (
              <div className="pt-4 space-y-3 border-t border-gray-200 dark:border-dark-700">
                <div className="px-4 py-2 bg-gray-50 dark:bg-dark-800 rounded-xl">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.fullName}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</p>
                </div>
                <button onClick={handleLogout} className="w-full px-6 py-3 text-red-600 dark:text-red-400 border border-red-300 dark:border-red-700 rounded-xl font-medium hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                  {t.nav.logout}
                </button>
              </div>
            ) : (
              <div className="pt-4 space-y-3">
                <button onClick={onLoginClick} className="w-full px-6 py-3 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-dark-700 rounded-xl font-medium hover:bg-gray-50 dark:hover:bg-dark-800 transition-colors">
                  {t.nav.login}
                </button>
                <button onClick={onSignupClick} className="w-full px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-xl font-medium shadow-lg">
                  {t.nav.getStarted}
                </button>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </motion.nav>
  )
}
