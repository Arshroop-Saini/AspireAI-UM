'use client';

import Link from 'next/link';
import { Space_Mono } from 'next/font/google';
import { PricingPlans } from '@/components/PricingPlans';
import { useSession } from 'next-auth/react';

// Use Space Mono font for the entire application
const spaceMono = Space_Mono({ 
  subsets: ['latin'],
  weight: ['400', '700']
});

const features = [
  {
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M8 14L12 10L16 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'College list generator',
    description: 'Get personalized college recommendations based on your profile and preferences',
    link: '/college-list'
  },
  {
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M8 2V5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M16 2V5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M3 9H21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M21 8V17C21 20 19.5 22 16 22H8C4.5 22 3 20 3 17V8C3 5 4.5 3 8 3H16C19.5 3 21 5 21 8Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M12 13H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M12 17H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M8 13H8.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M8 17H8.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'Essay brainstorming',
    description: 'Generate unique essay ideas tailored to your experiences and goals',
    link: '/essay-brainstorm'
  },
  {
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M8 12H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M8 16H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M8 8H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M3 20V4C3 2.89543 3.89543 2 5 2H19C20.1046 2 21 2.89543 21 4V20C21 21.1046 20.1046 22 19 22H5C3.89543 22 3 21.1046 3 20Z" stroke="currentColor" strokeWidth="1.5"/>
      </svg>
    ),
    title: 'Essay feedback',
    description: 'Receive detailed AI-powered critiques to improve your essays',
    link: '/essay-feedback'
  },
  {
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 7H21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M3 12H21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M3 17H21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    title: 'Activity optimizer',
    description: 'Discover and optimize extracurricular activities that align with your interests',
    link: '/ec-suggestions'
  },
  {
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M12 8V16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M8 12H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'Major match',
    description: 'Find the perfect major that aligns with your interests and career goals',
    link: '/major-suggestions'
  },
  {
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M12 6V12L16 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'Strategy planner',
    description: 'Get personalized guidance on your application timeline and strategy',
    link: '/strategy'
  }
];

const testimonials = [
  {
    quote: 'AspireAI helped me discover unique extracurricular activities that really made my application stand out. I got into my dream school!',
    name: 'Sarah L.',
    school: 'Accepted to Stanford',
    color: 'bg-[#1E1E1E]'
  },
  {
    quote: 'The essay feedback feature was a game-changer. It helped me refine my personal statement and make it truly compelling.',
    name: 'Michael R.',
    school: 'Accepted to Harvard',
    color: 'bg-[#1A1A1A]'
  },
  {
    quote: 'The college list generator saved me so much time and helped me find schools that were perfect matches for my interests and goals.',
    name: 'Emily W.',
    school: 'Accepted to MIT',
    color: 'bg-[#1E1E1E]'
  }
];

export default function Home() {
  const { data: session } = useSession();

  return (
    <div className={`min-h-screen bg-black text-white ${spaceMono.className}`}>
      {/* Header */}
      <header className="fixed top-0 w-full z-50 bg-black/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="bg-gradient-to-r from-[#E87C3E] to-[#FF8D4E] w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold">
              S
            </div>
            <span className="text-xl">ASPIREAI</span>
          </div>
          <nav className="hidden md:flex space-x-8">
            <a href="#features" className="text-gray-300 hover:text-white transition-colors">
              FEATURES
            </a>
            <a href="#testimonials" className="text-gray-300 hover:text-white transition-colors">
              TESTIMONIALS
            </a>
            <a href="#pricing" className="text-gray-300 hover:text-white transition-colors">
              PRICING
            </a>
          </nav>
          <Link 
            href={session ? "/dashboard" : "/auth/signin"}
            className="bg-[#E87C3E] hover:bg-[#FF8D4E] text-white px-6 py-2 rounded-lg transition-all duration-200"
          >
            {session ? "DASHBOARD" : "TRY NOW"}
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center">
        <div className="absolute inset-0 bg-gradient-radial from-[#E87C3E]/10 via-transparent to-transparent" />
        <div className="container mx-auto px-4 relative">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl lg:text-7xl leading-tight tracking-tight">
              Never stress about<br />college apps again
            </h1>
            <div className="mt-8">
              <Link
                href="/auth/signin"
                className="bg-[#E87C3E] hover:bg-[#FF8D4E] text-white px-8 py-3 rounded-lg transition-all duration-200 text-lg inline-flex items-center"
              >
                Get started <span className="ml-2">→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl md:text-4xl text-center mb-16">
            Features to supercharge your application
          </h2>
        </div>
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Link 
                key={index}
                href={feature.link}
                className="group relative p-8 rounded-2xl border border-gray-800 hover:border-[#E87C3E]/50 transition-all duration-300"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-[#E87C3E]/5 to-[#FF8D4E]/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="relative">
                  <div className="text-[#E87C3E] mb-6">
                    {feature.icon}
                  </div>
                  <h3 className="text-lg mb-4">{feature.title}</h3>
                  <p className="text-gray-400 text-sm">{feature.description}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl md:text-4xl text-center mb-16">
            What our students say
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {testimonials.map((testimonial, index) => (
              <div 
                key={index} 
                className="relative p-8 rounded-2xl border border-gray-800 bg-gradient-to-r from-black to-[#1A1A1A]"
              >
                <div className="text-[#E87C3E] text-4xl mb-6">&ldquo;</div>
                <p className="text-gray-300 text-sm mb-8">{testimonial.quote}</p>
                <div>
                  <div className="font-medium mb-1">{testimonial.name}</div>
                  <div className="text-[#E87C3E] text-sm">{testimonial.school}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl md:text-4xl text-center mb-16">
            Choose your plan
          </h2>
          <PricingPlans />
        </div>
      </section>
    </div>
  );
}
