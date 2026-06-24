import { motion } from 'framer-motion'
import { Scale, Gavel, FileText, Shield, Award, BookOpen } from 'lucide-react'

const icons = [Scale, Gavel, FileText, Shield, Award, BookOpen]

export default function AnimatedBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden opacity-20 dark:opacity-10">
      {Array.from({ length: 15 }).map((_, i) => {
        const Icon = icons[i % icons.length]
        const duration = 20 + Math.random() * 20
        const delay = Math.random() * 5
        const x = Math.random() * 100
        const size = 30 + Math.random() * 40
        
        return (
          <motion.div
            key={i}
            className="absolute"
            style={{
              left: `${x}%`,
              top: '-10%',
            }}
            animate={{
              y: ['0vh', '110vh'],
              rotate: [0, 360],
              opacity: [0, 0.3, 0.3, 0],
            }}
            transition={{
              duration,
              delay,
              repeat: Infinity,
              ease: 'linear',
            }}
          >
            <Icon 
              className="text-primary-500 dark:text-primary-400" 
              style={{ width: size, height: size }}
            />
          </motion.div>
        )
      })}
      
      {/* Floating emojis */}
      {['⚖️', '📜', '🏛️', '👨‍⚖️', '📚', '🔨'].map((emoji, i) => {
        const duration = 25 + Math.random() * 15
        const delay = Math.random() * 5
        const x = Math.random() * 100
        
        return (
          <motion.div
            key={`emoji-${i}`}
            className="absolute text-4xl"
            style={{
              left: `${x}%`,
              top: '-10%',
            }}
            animate={{
              y: ['0vh', '110vh'],
              x: [0, Math.sin(i) * 50, 0],
              rotate: [0, 360],
              opacity: [0, 0.4, 0.4, 0],
            }}
            transition={{
              duration,
              delay,
              repeat: Infinity,
              ease: 'linear',
            }}
          >
            {emoji}
          </motion.div>
        )
      })}
    </div>
  )
}
