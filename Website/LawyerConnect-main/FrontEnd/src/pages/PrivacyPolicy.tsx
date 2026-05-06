import { motion } from 'framer-motion'
import { Shield, Database, Eye, Lock } from 'lucide-react'
import { useEffect } from 'react'

export default function PrivacyPolicy() {
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
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-display font-bold mb-4 bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
            Privacy Policy
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
              At Estasheer, we take your privacy seriously. This Privacy Policy explains how we collect, use, and protect your information when you use our legal consultation platform.
            </p>
          </section>

          {/* Information We Collect */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <Database className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Information We Collect</h2>
            </div>
            <div className="space-y-4 text-gray-700 dark:text-gray-300">
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Personal Information</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Name, email, phone number, and city</li>
                  <li>Profile photo (optional)</li>
                  <li>For lawyers: Credentials, experience, specializations, address</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Usage Information</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Browser type, IP address, device information</li>
                  <li>Pages visited and features used</li>
                  <li>Booking and consultation history</li>
                </ul>
              </div>
            </div>
          </section>

          {/* How We Use Information */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <Eye className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">How We Use Your Information</h2>
            </div>
            <ul className="list-disc list-inside space-y-1 ml-4 text-gray-700 dark:text-gray-300">
              <li>Provide and improve our services</li>
              <li>Process bookings and facilitate consultations</li>
              <li>Send notifications about bookings and account activity</li>
              <li>Verify lawyer credentials</li>
              <li>Respond to support requests</li>
              <li>Detect and prevent fraud</li>
            </ul>
          </section>

          {/* Information Sharing */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Information Sharing</h2>
            <div className="space-y-3 text-gray-700 dark:text-gray-300">
              <p className="leading-relaxed font-semibold">We do not sell your personal information.</p>
              <p className="leading-relaxed">We may share information:</p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>With lawyers when you book a consultation</li>
                <li>With service providers who assist our operations</li>
                <li>When required by law or legal process</li>
                <li>In connection with business transfers</li>
              </ul>
            </div>
          </section>

          {/* Data Security */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <Lock className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Data Security</h2>
            </div>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              We implement appropriate security measures to protect your information. However, no method of transmission over the Internet is 100% secure.
            </p>
          </section>

          {/* Your Rights */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Your Rights</h2>
            <div className="space-y-2 text-gray-700 dark:text-gray-300">
              <p className="leading-relaxed">You have the right to:</p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>Access and receive a copy of your data</li>
                <li>Correct inaccurate information</li>
                <li>Request deletion of your data</li>
                <li>Object to certain processing</li>
                <li>Withdraw consent</li>
              </ul>
              <p className="leading-relaxed mt-4">
                Contact us at <a href="mailto:estasheer_support@gmail.com" className="text-primary-600 dark:text-primary-400 hover:underline">estasheer_support@gmail.com</a> to exercise these rights.
              </p>
            </div>
          </section>

          {/* Data Retention */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Data Retention</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              We retain your information as long as necessary to provide services, unless a longer period is required by law.
            </p>
          </section>

          {/* Children's Privacy */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Children's Privacy</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              Our services are not intended for individuals under 18. We do not knowingly collect information from children.
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
