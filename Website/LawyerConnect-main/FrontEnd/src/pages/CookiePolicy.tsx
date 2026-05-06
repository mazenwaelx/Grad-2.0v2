import { motion } from 'framer-motion'
import { Cookie, Info, Settings } from 'lucide-react'
import { useEffect } from 'react'

export default function CookiePolicy() {
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  return (
    <div className="min-h-screen pt-32 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Cookie className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-display font-bold mb-4 bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
            Cookie Policy
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-dark-800 rounded-3xl border border-gray-200 dark:border-dark-700 p-8 md:p-12 space-y-8"
        >
          {/* Introduction */}
          <section>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              This Cookie Policy explains how Estasheer uses cookies and similar technologies to improve your experience on our platform.
            </p>
          </section>

          {/* What Are Cookies */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <Info className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">What Are Cookies?</h2>
            </div>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              Cookies are small text files stored on your device when you visit a website. They help us remember your preferences and improve your experience.
            </p>
          </section>

          {/* Types of Cookies */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Types of Cookies We Use</h2>
            <div className="space-y-4 text-gray-700 dark:text-gray-300">
              <div className="bg-gray-50 dark:bg-dark-700 rounded-2xl p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Essential Cookies</h3>
                <p className="leading-relaxed mb-2">
                  Required for the platform to function. Cannot be disabled.
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                  <li>Authentication tokens</li>
                  <li>Session management</li>
                  <li>Security features</li>
                </ul>
              </div>

              <div className="bg-gray-50 dark:bg-dark-700 rounded-2xl p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Preference Cookies</h3>
                <p className="leading-relaxed mb-2">
                  Remember your choices for a personalized experience.
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                  <li>Language preference</li>
                  <li>Theme (light/dark mode)</li>
                  <li>UI settings</li>
                </ul>
              </div>

              <div className="bg-gray-50 dark:bg-dark-700 rounded-2xl p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Performance Cookies</h3>
                <p className="leading-relaxed mb-2">
                  Help us understand how you use our platform.
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                  <li>Page load times</li>
                  <li>Error tracking</li>
                  <li>Usage patterns</li>
                </ul>
              </div>

              <div className="bg-gray-50 dark:bg-dark-700 rounded-2xl p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Functional Cookies</h3>
                <p className="leading-relaxed mb-2">
                  Enable enhanced functionality through caching.
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                  <li>Cached lawyer listings</li>
                  <li>Cached booking data</li>
                  <li>Session storage</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Third-Party Cookies */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Third-Party Cookies</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              We do not currently use third-party cookies for advertising or tracking. All cookies are first-party cookies set by Estasheer.
            </p>
          </section>

          {/* Managing Cookies */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <Settings className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Managing Cookies</h2>
            </div>
            <div className="space-y-4 text-gray-700 dark:text-gray-300">
              <p className="leading-relaxed">
                You can control cookies through your browser settings:
              </p>
              
              <div className="bg-primary-50 dark:bg-primary-900/20 rounded-2xl p-6 border border-primary-200 dark:border-primary-800">
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li><strong>Chrome:</strong> Settings → Privacy → Cookies</li>
                  <li><strong>Firefox:</strong> Options → Privacy & Security</li>
                  <li><strong>Safari:</strong> Preferences → Privacy</li>
                  <li><strong>Edge:</strong> Settings → Cookies and site permissions</li>
                </ul>
              </div>

              <p className="leading-relaxed text-sm">
                Note: Blocking cookies may affect platform functionality.
              </p>
            </div>
          </section>

          {/* Local Storage */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Local & Session Storage</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              We use browser storage to cache data and improve performance. You can clear this data through your browser settings or by logging out.
            </p>
          </section>

          {/* Contact */}
          <section className="pt-6 border-t border-gray-200 dark:border-dark-700">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Contact Us</h2>
            <ul className="space-y-2 text-gray-700 dark:text-gray-300">
              <li>Email: <a href="mailto:estasheer_support@gmail.com" className="text-primary-600 dark:text-primary-400 hover:underline">estasheer_support@gmail.com</a></li>
              <li>Phone: <a href="tel:+201234567890" className="text-primary-600 dark:text-primary-400 hover:underline">+20 123 456 7890</a></li>
            </ul>
          </section>
        </motion.div>
      </div>
    </div>
  )
}
