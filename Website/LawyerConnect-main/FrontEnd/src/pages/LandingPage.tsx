import Hero from '../components/Hero'
import Features from '../components/Features'
import LawyersSection from '../components/LawyersSection'
import HowItWorks from '../components/HowItWorks'
import Testimonials from '../components/Testimonials'
import CTASection from '../components/CTASection'

interface LandingPageProps {
  onGetStarted: () => void
}

export default function LandingPage({ onGetStarted }: LandingPageProps) {
  return (
    <>
      <Hero onGetStarted={onGetStarted} />
      <Features />
      <LawyersSection />
      <HowItWorks />
      <Testimonials />
      <CTASection onGetStarted={onGetStarted} />
    </>
  )
}
