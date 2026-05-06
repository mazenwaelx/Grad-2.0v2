import { motion } from 'framer-motion'
import { UserPlus, Search, Calendar, MessageSquare } from 'lucide-react'

const steps = [
  {
    icon: UserPlus,
    title: 'Create Account',
    description: 'Sign up in seconds with your email or social account'
  },
  {
    icon: Search,
    title: 'Find Your Lawyer',
    description: 'Browse verified lawyers by specialty and location'
  },
  {
    icon: Calendar,
    title: 'Book Consultation',
    description: 'Schedule a meeting at your convenient time'
  },
  {
    icon: MessageSquare,
    title: 'Get Legal Help',
    description: 'Connect with your lawyer and get expert advice'
  }
]

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 bg-gray-50 dark:bg-dark-900/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-display font-bold mb-4">
            <span className="bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
              How It Works
            </span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Get legal help in four simple steps
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="relative text-center"
            >
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-700 rounded-3xl mb-6 shadow-xl">
                <step.icon className="w-10 h-10 text-white" />
              </div>
              <div className="absolute top-10 left-1/2 -translate-x-1/2 w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center text-sm font-bold text-primary-700 dark:text-primary-300">
                {index + 1}
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                {step.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
