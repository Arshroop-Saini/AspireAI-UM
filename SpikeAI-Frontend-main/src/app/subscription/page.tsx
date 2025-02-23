'use client';

import { useSession } from 'next-auth/react';
import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { mono } from '@/lib/fonts';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Check } from 'lucide-react';

interface StudentSubscription {
    is_subscribed: boolean;
    status: string;
    stripe_customer_id: string | null;
    stripe_subscription_id: string | null;
    plan_type: string | null;
    current_period_start: string | null;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
    payment_status: string | null;
    last_payment_date: string | null;
    features: string[];
}

const features = [
    'AI College List Generation',
    'Extracurricular Activity Suggestions',
    'Essay Feedback & Analysis',
    'Essay Topic Brainstorming',
    'Profile Evaluation',
    'Regular Updates & New Features',
    'Priority Support'
];

export default function SubscriptionPage() {
    const { data: session } = useSession();
    const [loading, setLoading] = useState(false);
    const [subscription, setSubscription] = useState<StudentSubscription | null>(null);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();
    const searchParams = useSearchParams();

    const fetchSubscriptionStatus = async () => {
        try {
            const response = await fetch('/api/payment/subscription-status', {
                headers: {
                    'Authorization': `Bearer ${session?.id_token}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                setSubscription(data.subscription);
            }
        } catch (error) {
            console.error('Error fetching subscription:', error);
        }
    };

    useEffect(() => {
        if (!searchParams) return;
        const sessionId = searchParams.get('session_id');
        if (sessionId) {
            verifySubscription(sessionId);
        }
    }, [searchParams]);

    useEffect(() => {
        if (session) {
            fetchSubscriptionStatus();
        }
    }, [session]);

    const verifySubscription = async (sessionId: string) => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`/api/payment/verify-subscription?session_id=${sessionId}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to verify subscription');
            }
            
            setSubscription(data);
            router.push('/dashboard');
        } catch (error) {
            console.error('Subscription verification error:', error);
            setError(error instanceof Error ? error.message : 'Failed to verify subscription');
        } finally {
            setLoading(false);
        }
    };

    const handleSubscribe = async (plan_type: 'monthly' | 'yearly') => {
        try {
            setLoading(true);
            const response = await fetch('/api/subscription/create-checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ plan_type })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to create subscription');
            }

            window.location.href = data.url;
        } catch (error) {
            console.error('Subscription error:', error);
            alert('Failed to process subscription request');
        } finally {
            setLoading(false);
        }
    };

    const handleManageSubscription = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/subscription/create-portal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const { url } = await response.json();
            if (url) {
                window.location.href = url;
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load subscription management');
        } finally {
            setLoading(false);
        }
    };

    if (subscription?.is_subscribed && subscription?.status === 'active') {
        return (
            <div className="min-h-screen bg-black">
                <div className="container mx-auto px-4 py-8">
                    <Card className="max-w-2xl mx-auto border-zinc-800/40 bg-[#0A0A0B]">
                        <CardHeader>
                            <CardTitle className={`text-white ${mono.className}`}>
                                <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                                Current Subscription
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className={`p-4 rounded-lg ${
                                subscription.status === 'active' 
                                    ? 'bg-[#18181B] border-zinc-800/40' 
                                    : 'bg-yellow-500/10 border-yellow-500/20'
                            } border`}>
                                <div className="flex items-center">
                                    <div className={`w-2 h-2 rounded-full mr-2 ${
                                        subscription.status === 'active' ? 'bg-[#E87C3E]' : 'bg-yellow-500'
                                    }`} />
                                    <p className={`text-white ${mono.className}`}>
                                        {subscription.status === 'active' 
                                            ? `Active ${subscription.plan_type ?? ''} Plan`
                                            : `Subscription Status: ${subscription.status}`}
                                    </p>
                                </div>
                                {subscription.current_period_end && (
                                    <p className={`text-sm text-zinc-400 mt-2 ${mono.className}`}>
                                        Next billing date: {new Date(subscription.current_period_end).toLocaleDateString()}
                                    </p>
                                )}
                                {subscription.cancel_at_period_end && (
                                    <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                                        <p className={`text-white ${mono.className}`}>
                                            Your subscription will end on {new Date(subscription.current_period_end!).toLocaleDateString()}
                                        </p>
                                        <p className={`text-sm text-zinc-400 mt-2 ${mono.className}`}>
                                            You can reactivate your subscription before this date to maintain access.
                                        </p>
                                    </div>
                                )}
                            </div>
                            <div className="flex flex-col gap-4">
                                <Button
                                    onClick={handleManageSubscription}
                                    disabled={loading}
                                    className="bg-[#E87C3E] hover:bg-[#FF8D4E] text-white w-full"
                                >
                                    {loading ? 'Loading...' : 'Manage Subscription'}
                                </Button>
                                <Button
                                    onClick={() => router.push('/dashboard')}
                                    variant="outline"
                                    className="w-full border-zinc-800 text-zinc-400 hover:text-white"
                                >
                                    Return to Dashboard
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black">
            <div className="container mx-auto px-4 py-8">
                {loading && (
                    <div className="text-center py-4">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#E87C3E] mx-auto"></div>
                        <p className={`mt-2 text-zinc-400 ${mono.className}`}>Processing...</p>
                    </div>
                )}
                {error && (
                    <div className="max-w-2xl mx-auto mb-8 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                        <p className={`text-white ${mono.className}`}>{error}</p>
                    </div>
                )}
                <div className="max-w-4xl mx-auto text-center mb-12">
                    <h1 className={`text-3xl font-bold text-white mb-4 ${mono.className}`}>Choose Your Plan</h1>
                    <p className={`text-zinc-400 ${mono.className}`}>
                        Get access to all our AI-powered tools to enhance your college application
                    </p>
                </div>
                
                <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
                    {/* Monthly Plan */}
                    <Card className="border-zinc-800/40 bg-[#0A0A0B] relative">
                        <CardHeader>
                            <CardTitle className={`text-white ${mono.className}`}>Monthly Plan</CardTitle>
                            <div className={`text-3xl font-bold text-white mt-2 ${mono.className}`}>
                                $19<span className="text-lg font-normal text-zinc-400">/month</span>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <ul className="space-y-3">
                                {features.map((feature, index) => (
                                    <li key={index} className="flex items-center">
                                        <Check className="h-4 w-4 text-[#E87C3E] mr-2" />
                                        <span className={`text-zinc-400 ${mono.className}`}>{feature}</span>
                                    </li>
                                ))}
                            </ul>
                            <Button
                                onClick={() => handleSubscribe('monthly')}
                                disabled={loading}
                                className="w-full bg-[#E87C3E] hover:bg-[#FF8D4E] text-white"
                            >
                                {loading ? 'Processing...' : 'Subscribe Monthly'}
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Yearly Plan */}
                    <Card className="border-zinc-800/40 bg-[#0A0A0B] relative">
                        <div className="absolute -top-3 right-4 bg-[#E87C3E] text-white text-xs px-3 py-1 rounded-full">
                            SAVE 17%
                        </div>
                        <CardHeader>
                            <CardTitle className={`text-white ${mono.className}`}>Yearly Plan</CardTitle>
                            <div className={`text-3xl font-bold text-white mt-2 ${mono.className}`}>
                                $154<span className="text-lg font-normal text-zinc-400">/year</span>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <ul className="space-y-3">
                                {features.map((feature, index) => (
                                    <li key={index} className="flex items-center">
                                        <Check className="h-4 w-4 text-[#E87C3E] mr-2" />
                                        <span className={`text-zinc-400 ${mono.className}`}>{feature}</span>
                                    </li>
                                ))}
                            </ul>
                            <Button
                                onClick={() => handleSubscribe('yearly')}
                                disabled={loading}
                                className="w-full bg-[#E87C3E] hover:bg-[#FF8D4E] text-white"
                            >
                                {loading ? 'Processing...' : 'Subscribe Yearly'}
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
} 