import { motion } from 'framer-motion'
import { FileText, CheckCircle, Scale } from 'lucide-react'
import { useEffect } from 'react'

export default function TermsOfService() {
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
            <FileText className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-display font-bold mb-4 bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
            Terms of Service
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
              Welcome to Estasheer. By using our platform, you agree to these Terms of Service. Estasheer is a free legal consultation platform connecting clients with verified lawyers.
            </p>
          </section>

          {/* Acceptance */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Acceptance of Terms</h2>
            </div>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              By creating an account, you confirm you are at least 18 years old and agree to these Terms and our Privacy Policy.
            </p>
          </section>

          {/* Platform */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <Scale className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Platform Services</h2>
            </div>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
              Estasheer is a free platform that connects clients with verified lawyers. We facilitate bookings and communications but do not provide legal services ourselves.
            </p>
            <ul className="list-disc list-inside space-y-1 ml-4 text-gray-700 dark:text-gray-300">
              <li>Free for both clients and lawyers</li>
              <li>No commissions or subscription fees</li>
              <li>Lawyers set their own consultation fees</li>
              <li>Payments handled directly between parties</li>
            </ul>
          </section>

          {/* User Accounts */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">User Responsibilities</h2>
            <div className="space-y-2 text-gray-700 dark:text-gray-300">
              <p className="leading-relaxed">You agree to:</p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>Provide accurate and current information</li>
                <li>Maintain account security</li>
                <li>Accept responsibility for all account activities</li>
                <li>Notify us of unauthorized access</li>
              </ul>
            </div>
          </section>

          {/* Lawyer Verification */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Lawyer Verification</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              Lawyers must provide accurate credentials. We verify all lawyer profiles before approval. Providing false information may result in account termination.
            </p>
          </section>

          {/* Bookings */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Bookings & Consultations</h2>
            <ul className="list-disc list-inside space-y-1 ml-4 text-gray-700 dark:text-gray-300">
              <li>Clients book consultations through our platform</li>
              <li>Lawyers set their own availability and pricing</li>
              <li>Cancellations require 24 hours advance notice</li>
              <li>Lawyers may confirm, reschedule, or decline requests</li>
            </ul>
          </section>

          {/* Prohibited Conduct */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Prohibited Conduct</h2>
            <div className="space-y-2 text-gray-700 dark:text-gray-300">
              <p className="leading-relaxed">You may not:</p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>Use the platform for illegal purposes</li>
                <li>Impersonate others or provide false information</li>
                <li>Harass or harm other users</li>
                <li>Interfere with platform operations</li>
                <li>Attempt unauthorized access</li>
              </ul>
            </div>
          </section>

          {/* Disclaimer */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Disclaimer</h2>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-2xl p-6">
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                THE PLATFORM IS PROVIDED "AS IS" WITHOUT WARRANTIES. Estasheer is a connection platform only - we do not provide legal advice or services. We are not responsible for the quality or legality of services provided by lawyers on our platform.
              </p>
            </div>
          </section>

          {/* Limitation of Liability */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Limitation of Liability</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              Estasheer shall not be liable for any indirect, incidental, or consequential damages arising from your use of the platform.
            </p>
          </section>

          {/* Termination */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Termination</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              We may suspend or terminate your account for violations of these Terms. You may delete your account at any time through account settings.
            </p>
          </section>

          {/* Governing Law */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Governing Law</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              These Terms are governed by the laws of Egypt. Disputes shall be subject to the jurisdiction of Cairo courts.
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
