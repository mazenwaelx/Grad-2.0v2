import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { useAuth } from './contexts/AuthContext'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import LoginModal from './components/LoginModal'
import SignupModal from './components/SignupModal'
import AIChatModal from './components/AIChatModal'
import AnimatedBackground from './components/AnimatedBackground'
import LandingPage from './pages/LandingPage'
import BrowseLawyers from './pages/BrowseLawyers'
import LawyerProfile from './pages/LawyerProfile'
import UserDashboard from './pages/UserDashboard'
import LawyerDashboard from './pages/LawyerDashboard'
import AccountPage from './pages/AccountPage'
import AdminDashboard from './pages/AdminDashboard'
import PrivacyPolicy from './pages/PrivacyPolicy'
import TermsOfService from './pages/TermsOfService'
import CookiePolicy from './pages/CookiePolicy'

function App() {
  const { isLoggedIn, user } = useAuth()
  const [isDark, setIsDark] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [showSignup, setShowSignup] = useState(false)
  const [showAIChat, setShowAIChat] = useState(false)

  useEffect(() => {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      setIsDark(true)
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleTheme = () => {
    setIsDark(!isDark)
    if (!isDark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-dark-950 dark:via-dark-900 dark:to-dark-950 relative">
        <AnimatedBackground />
        
        <Navbar 
          isDark={isDark} 
          toggleTheme={toggleTheme}
          onLoginClick={() => setShowLogin(true)}
          onSignupClick={() => setShowSignup(true)}
          onAIChatClick={() => setShowAIChat(true)}
        />
        
        <main>
          <Routes>
            <Route path="/" element={<LandingPage onGetStarted={() => setShowSignup(true)} />} />
            <Route path="/lawyers" element={<BrowseLawyers />} />
            <Route path="/lawyer/:id" element={<LawyerProfile />} />
            <Route path="/privacy-policy" element={<PrivacyPolicy />} />
            <Route path="/terms-of-service" element={<TermsOfService />} />
            <Route path="/cookie-policy" element={<CookiePolicy />} />
            <Route 
              path="/dashboard" 
              element={
                isLoggedIn ? (
                  user?.role === 'Lawyer' ? <LawyerDashboard /> : <UserDashboard />
                ) : (
                  <Navigate to="/" replace />
                )
              } 
            />
            <Route 
              path="/account" 
              element={
                isLoggedIn ? <AccountPage /> : <Navigate to="/" replace />
              } 
            />
            <Route 
              path="/admin" 
              element={
                isLoggedIn && user?.role === 'Admin' ? <AdminDashboard /> : <Navigate to="/" replace />
              } 
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        <Footer />

        <AnimatePresence>
          {showLogin && (
            <LoginModal 
              onClose={() => setShowLogin(false)}
              onSwitchToSignup={() => {
                setShowLogin(false)
                setShowSignup(true)
              }}
            />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {showSignup && (
            <SignupModal 
              onClose={() => setShowSignup(false)}
              onSwitchToLogin={() => {
                setShowSignup(false)
                setShowLogin(true)
              }}
            />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {showAIChat && (
            <AIChatModal onClose={() => setShowAIChat(false)} />
          )}
        </AnimatePresence>
      </div>
    </Router>
  )
}

export default App