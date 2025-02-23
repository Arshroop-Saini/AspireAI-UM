'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { mono } from '@/lib/fonts';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';

interface SubscriptionDetails {
    is_subscribed: boolean;
    status: string;
    plan_type?: string;
    current_period_start?: string;
    current_period_end?: string;
    stripe_customer_id?: string;
    stripe_subscription_id?: string;
    cancel_at_period_end?: boolean;
    payment_status?: string;
    last_payment_date?: string;
    features?: string[];
}

export default function SettingsPage() {
    const { data: session } = useSession();
    const router = useRouter();
    const { toast } = useToast();
    const [loading, setLoading] = useState(false);
    const [subscription, setSubscription] = useState<SubscriptionDetails | null>(null);

    useEffect(() => {
        fetchSubscriptionStatus();
    }, []);

    const fetchSubscriptionStatus = async () => {
        try {
            const response = await fetch('/api/subscription/status');
            const data = await response.json();
            
            if (!data.success) {
                console.error('Subscription error:', data.error);
                setSubscription(null);
                return;
            }

            if (data.subscription) {
                setSubscription(data.subscription);
            } else {
                setSubscription(null);
            }
        } catch (error) {
            console.error('Error fetching subscription:', error);
            setSubscription(null);
        }
    };

    const handleManageSubscription = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/subscription/portal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to load subscription management');
            }
            
            if (data.url) {
                window.location.href = data.url;
            }
        } catch (error) {
            console.error('Error:', error);
            toast({
                title: 'Error',
                description: error instanceof Error ? error.message : 'Failed to load subscription management',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('/api/profile', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to delete account');
            }

            toast({
                title: 'Account deleted',
                description: 'Your account has been successfully deleted.',
            });

            router.push('/auth/signin');
        } catch (error) {
            toast({
                title: 'Error',
                description: 'Failed to delete account. Please try again.',
                variant: 'destructive',
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black">
            <div className="container mx-auto px-4 py-8">
                <h1 className={`text-2xl font-bold mb-8 text-white ${mono.className}`}>Settings</h1>

                {/* Account Settings */}
                <Card className="border-zinc-800/40 bg-[#0A0A0B] mb-8">
                    <CardHeader>
                        <CardTitle className={`text-white ${mono.className}`}>
                            <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                            Account Settings
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* User Info */}
                        <div className="p-4 rounded-lg bg-[#18181B] border border-zinc-800/40">
                            <div className="flex items-center space-x-4">
                                <div className="h-12 w-12 rounded-full bg-[#E87C3E] flex items-center justify-center text-white text-xl">
                                    {session?.user?.name?.[0] || 'U'}
                                </div>
                                <div>
                                    <p className={`text-white ${mono.className}`}>{session?.user?.name}</p>
                                    <p className={`text-sm text-zinc-400 ${mono.className}`}>{session?.user?.email}</p>
                                </div>
                            </div>
                        </div>

                        {/* Danger Zone */}
                        <div className="space-y-4">
                            <h3 className={`text-lg text-red-500 ${mono.className}`}>Danger Zone</h3>
                            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className={`text-white ${mono.className}`}>Delete Account</p>
                                        <p className={`text-sm text-zinc-400 ${mono.className}`}>Permanently delete your account and all data</p>
                                    </div>
                                    <Button
                                        onClick={handleDeleteAccount}
                                        disabled={loading}
                                        className="bg-red-500 hover:bg-red-600 text-white"
                                    >
                                        {loading ? 'Deleting...' : 'Delete Account'}
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Subscription Settings */}
                <Card className="border-zinc-800/40 bg-[#0A0A0B]">
                    <CardHeader>
                        <CardTitle className={`text-white ${mono.className}`}>
                            <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                            Subscription
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {subscription?.is_subscribed ? (
                            <div className="space-y-6">
                                {/* Subscription Status */}
                                <div className={`p-4 rounded-lg ${
                                    subscription.status === 'active' 
                                        ? 'bg-[#18181B] border-zinc-800/40' 
                                        : 'bg-yellow-500/10 border-yellow-500/20'
                                } border`}>
                                    <div className="flex items-center justify-between">
                                        <div>
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
                                        </div>
                                        <Button
                                            onClick={handleManageSubscription}
                                            disabled={loading}
                                            className="bg-[#E87C3E] hover:bg-[#FF8D4E] text-white"
                                        >
                                            {loading ? 'Loading...' : 'Manage Subscription'}
                                        </Button>
                                    </div>
                                </div>

                                {/* Cancellation Notice */}
                                {subscription.cancel_at_period_end && subscription.current_period_end && (
                                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                                        <p className={`text-white ${mono.className}`}>
                                            Your subscription will end on {new Date(subscription.current_period_end).toLocaleDateString()}
                                        </p>
                                        <p className={`text-sm text-zinc-400 mt-2 ${mono.className}`}>
                                            You can reactivate your subscription before this date to maintain access.
                                        </p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="p-4 rounded-lg bg-[#18181B] border border-zinc-800/40">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className={`text-white ${mono.className}`}>Current Plan</p>
                                        <p className={`text-sm text-zinc-400 ${mono.className}`}>Free Plan</p>
                                    </div>
                                    <Button
                                        onClick={() => router.push('/pricing')}
                                        className="bg-[#E87C3E] hover:bg-[#FF8D4E] text-white"
                                    >
                                        Upgrade Plan
                                    </Button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
} 