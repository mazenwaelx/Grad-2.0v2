import { Scale, Mail, Phone, MapPin } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext'

export default function Footer() {
  const { t } = useLanguage()
  const navigate = useNavigate()

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    } else {
      // If not on home page, navigate to home first
      navigate('/')
      setTimeout(() => {
        const el = document.getElementById(sectionId)
        if (el) el.scrollIntoView({ behavior: 'smooth' })
      }, 100)
    }
  }
  
  return (
    <footer className="bg-gray-50 dark:bg-dark-900 border-t border-gray-200 dark:border-dark-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center">
                <Scale className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-display font-bold bg-gradient-to-r from-primary-600 to-primary-800 dark:from-primary-400 dark:to-primary-600 bg-clip-text text-transparent">
                Estasheer
              </span>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {t.footer.tagline}
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">{t.footer.quickLinks}</h3>
            <ul className="space-y-2">
              <li>
                <button 
                  onClick={() => scrollToSection('features')}
                  className="text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                >
                  {t.footer.aboutUs}
                </button>
              </li>
              <li>
                <button 
                  onClick={() => scrollToSection('how-it-works')}
                  className="text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                >
                  {t.footer.howItWorks}
                </button>
              </li>
              <li>
                <button 
                  onClick={() => navigate('/lawyers')}
                  className="text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                >
                  Browse Lawyers
                </button>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">{t.footer.legal}</h3>
            <ul className="space-y-2">
              <li>
                <button 
                  onClick={() => navigate('/privacy-policy')}
                  className="text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                >
                  {t.footer.privacyPolicy}
                </button>
              </li>
              <li>
                <button 
                  onClick={() => navigate('/terms-of-service')}
                  className="text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                >
                  {t.footer.termsOfService}
                </button>
              </li>
              <li>
                <button 
                  onClick={() => navigate('/cookie-policy')}
                  className="text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                >
                  {t.footer.cookiePolicy}
                </button>
              </li>
            </ul>
          </div>

          {/* Contact Us */}
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Contact Us</h3>
            <ul className="space-y-3">
              <li className="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm">
                <Mail className="w-4 h-4 flex-shrink-0" />
                <a href="mailto:estasheer_support@gmail.com" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                  estasheer_support@gmail.com
                </a>
              </li>
              <li className="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm">
                <Phone className="w-4 h-4 flex-shrink-0" />
                <a href="tel:+201234567890" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                  +20 123 456 7890
                </a>
              </li>
              <li className="flex items-start gap-2 text-gray-600 dark:text-gray-400 text-sm">
                <MapPin className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>Cairo, Egypt</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-200 dark:border-dark-800 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            © 2024 Estasheer. {t.footer.allRightsReserved}
          </p>
          <p className="text-gray-500 dark:text-gray-500 text-xs">
            Free legal consultation platform
          </p>
        </div>
      </div>
    </footer>
  )
}
