'use client';

import { 
  AcademicCapIcon, 
  DocumentTextIcon, 
  ChatBubbleBottomCenterTextIcon, 
  ListBulletIcon,
  LightBulbIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const features = [
  {
    title: 'College list generator',
    description: 'Get personalized college recommendations based on your profile and preferences',
    icon: AcademicCapIcon,
  },
  {
    title: 'Essay brainstorming',
    description: 'Generate unique essay ideas tailored to your experiences and goals',
    icon: DocumentTextIcon,
  },
  {
    title: 'Essay feedback',
    description: 'Receive detailed AI-powered critiques to improve your essays',
    icon: ChatBubbleBottomCenterTextIcon,
  },
  {
    title: 'Activity optimizer',
    description: 'Discover and optimize extracurricular activities that align with your interests',
    icon: ListBulletIcon,
  },
  {
    title: 'Major match',
    description: 'Find the perfect major that aligns with your interests and career goals',
    icon: LightBulbIcon,
  },
  {
    title: 'Strategy planner',
    description: 'Get personalized guidance on your application timeline and strategy',
    icon: ArrowPathIcon,
  },
];

export function Features() {
  return (
    <section className="py-24">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">
            Everything you need
          </h2>
          <p className="text-gray-300 text-lg">
            Comprehensive tools to help you succeed in your college applications
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-dark-300 rounded-xl p-6 hover:bg-dark-200 transition-colors"
            >
              <div className="w-12 h-12 bg-primary-500/10 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-primary-500" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-300">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
} 
