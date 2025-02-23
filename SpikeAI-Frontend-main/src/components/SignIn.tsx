'use client';

import { signIn, useSession } from 'next-auth/react';
import { useState, useEffect } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { JetBrains_Mono } from 'next/font/google';

const mono = JetBrains_Mono({ 
    subsets: ['latin'],
    variable: '--font-mono'
});

export default function SignIn() {
    const { data: session, status } = useSession();
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (status === 'authenticated' && session) {
            router.replace('/dashboard');
        }
    }, [status, session, router]);

    // Show loading state while checking session
    if (status === 'loading') {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#E87C3E]"></div>
            </div>
        );
    }

    const handleGoogleSignIn = async () => {
        try {
            setLoading(true);
            setError(null);

            await signIn('google', {
                callbackUrl: '/dashboard',
                redirect: true
            });

        } catch (error) {
            console.error('Sign-in error:', error);
            setError('Failed to sign in');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={`flex flex-col items-center justify-center min-h-screen p-4 bg-black ${mono.className}`}>
            <div className="w-full max-w-md space-y-12">
                <div className="text-center">
                    <h1 className="text-4xl font-bold text-white">
                        <span className="text-[#E87C3E]">Aspire</span>AI
                    </h1>
                </div>

                {error && (
                    <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-lg text-sm">
                        {error}
                    </div>
                )}

                <button
                    onClick={handleGoogleSignIn}
                    disabled={loading}
                    className="w-full flex items-center justify-center gap-3 bg-[#18181B] text-white/80 px-6 py-4 rounded-lg border border-zinc-800 hover:border-zinc-600 hover:text-white transition-all duration-200 disabled:opacity-50 disabled:hover:border-zinc-800"
                >
                    {loading ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#E87C3E]"></div>
                    ) : (
                        <>
                            <Image 
                                src="/google.svg" 
                                alt="Google" 
                                width={20} 
                                height={20} 
                            />
                            Continue with Google
                        </>
                    )}
                </button>
            </div>
        </div>
    );
} 
