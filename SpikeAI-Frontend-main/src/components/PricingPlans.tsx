'use client';

import Link from 'next/link';

const plans = [
  {
    name: 'Monthly',
    price: '$19',
    period: '/month',
    cta: 'Start Monthly Plan',
    href: '/auth/signup?plan=monthly',
    highlighted: false
  },
  {
    name: 'Yearly',
    price: '$154',
    period: '/year',
    cta: 'Start Yearly Plan',
    href: '/auth/signup?plan=yearly',
    highlighted: true
  }
];

export function PricingPlans() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
      {plans.map((plan) => (
        <div
          key={plan.name}
          className={`relative p-8 rounded-2xl border ${
            plan.highlighted 
              ? 'border-[#E87C3E] bg-gradient-to-r from-black to-[#1A1A1A]' 
              : 'border-gray-800 bg-gradient-to-r from-black to-[#1A1A1A] hover:border-[#E87C3E]/50'
          } transition-all duration-300`}
        >
          {plan.highlighted && (
            <div className="absolute -top-3 right-4 bg-[#E87C3E] text-white text-xs px-3 py-1 rounded-full">
              BEST VALUE
            </div>
          )}
          <div className="flex flex-col h-full">
            <h3 className="text-xl text-white mb-2">{plan.name}</h3>
            <div className="flex items-baseline mb-8">
              <span className="text-4xl text-white font-light">{plan.price}</span>
              <span className="text-gray-400 ml-2">{plan.period}</span>
            </div>
            <Link
              href={plan.href}
              className={`mt-auto text-center py-3 px-6 rounded-lg transition-all duration-200 ${
                plan.highlighted
                  ? 'bg-[#E87C3E] hover:bg-[#FF8D4E] text-white'
                  : 'border border-[#E87C3E] text-[#E87C3E] hover:bg-[#E87C3E] hover:text-white'
              }`}
            >
              {plan.cta}
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
} 