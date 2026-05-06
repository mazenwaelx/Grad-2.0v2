import { motion } from 'framer-motion'
import { Bot, Users, Clock, Shield, MessageSquare, Award } from 'lucide-react'

const features = [
  {
    icon: Bot,
    title: 'AI Legal Assistant',
    description: 'Get instant answers to your legal questions 24/7 with our advanced AI chatbot.',
    color: 'from-blue-500 to-blue-700'
  },
  {
    icon: Users,
    title: 'Expert Lawyers',
    description: 'Connect with verified, experienced lawyers across multiple specializations.',
    color: 'from-purple-500 to-purple-700'
  },
  {
    icon: Clock,
    title: 'Quick Booking',
    description: 'Schedule consultations in minutes with our streamlined booking system.',
    color: 'from-green-500 to-green-700'
  },
  {
    icon: Shield,
    title: 'Secure & Private',
    description: 'Your data is encrypted and protected with enterprise-grade security.',
    color: 'from-red-500 to-red-700'
  },
  {
    icon: MessageSquare,
    title: 'Real-time Chat',
    description: 'Communicate with lawyers through our secure messaging platform.',
    color: 'from-yellow-500 to-yellow-700'
  },
  {
    icon: Award,
    title: 'Verified Professionals',
    description: 'All lawyers are thoroughly vetted and certified by our team.',
    color: 'from-primary-500 to-primary-700'
  }
]

export default function Features() {
  return (
    <section id="features" className="py-24 bg-gray-50 dark:bg-dark-900/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-display font-bold mb-4">
            <span className="bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
              Everything You Need
            </span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Powerful features to make legal consultation simple, fast, and accessible
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -5 }}
              className="group p-8 bg-white dark:bg-dark-800 rounded-3xl border border-gray-200 dark:border-dark-700 hover:border-primary-500 dark:hover:border-primary-500 transition-all hover:shadow-2xl"
            >
              <div className={`w-14 h-14 bg-gradient-to-br ${feature.color} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                <feature.icon className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                {feature.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
