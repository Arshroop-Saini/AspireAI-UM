'use client';

import { Button } from '@/components/ui/button';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export function Hero() {
  const { data: session } = useSession();
  const router = useRouter();

  const handleClick = () => {
    if (session) {
      router.push('/dashboard');
    } else {
      router.push('/auth/signin');
    }
  };

  return (
    <section className="relative pt-32 pb-24 overflow-hidden">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-4xl mx-auto">
          <div className="mb-8">
            <span className="inline-block px-3 py-1 text-sm text-primary-500 bg-primary-500/10 rounded-full">
              Backed by Y Combinator
            </span>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Never stress about
            <br />
            college apps again
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            Your AI-powered college application assistant that
            helps you craft the perfect application
          </p>
          <Button size="lg" className="font-semibold" onClick={handleClick}>
            {session ? 'Go to Dashboard →' : 'Get Started →'}
          </Button>
        </div>
      </div>
      
      {/* Background gradient effect */}
      <div className="absolute inset-0 -z-10 bg-gradient-dark" />
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_center,rgba(255,69,0,0.1),transparent_50%)]" />
    </section>
  );
} 
