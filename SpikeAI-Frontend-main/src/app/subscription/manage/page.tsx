'use client';

import { useSession } from 'next-auth/react';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface SubscriptionDetails {
    is_subscribed: boolean;
    status: string;
    plan: string;
    current_period_end?: string;
    cancel_at_period_end?: boolean;
}

export default function ManageSubscriptionPage() {
    const { data: session } = useSession();
    const [loading, setLoading] = useState(false);
    const [subscription, setSubscription] = useState<SubscriptionDetails | null>(null);
    const router = useRouter();

    useEffect(() => {
        fetchSubscriptionStatus();
    }, []);

    const fetchSubscriptionStatus = async () => {
        try {
            const response = await fetch('/api/subscription/status');
            if (response.ok) {
                const data = await response.json();
                setSubscription(data);
            }
        } catch (error) {
            console.error('Error fetching subscription:', error);
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

    if (!subscription?.is_subscribed) {
        return (
            <div className="max-w-4xl mx-auto p-6">
                <div className="bg-yellow-50 text-yellow-800 p-4 rounded-md mb-4">
                    <p>You don't have an active subscription.</p>
                </div>
                <button
                    onClick={() => router.push('/subscription')}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md"
                >
                    View Plans
                </button>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-6">
            <h1 className="text-3xl font-bold mb-6">Manage Subscription</h1>
            
            <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4">Current Plan</h2>
                <div className="space-y-2 mb-6">
                    <p><span className="font-medium">Plan:</span> {subscription.plan}</p>
                    <p><span className="font-medium">Status:</span> {subscription.status}</p>
                    {subscription.current_period_end && (
                        <p>
                            <span className="font-medium">Next billing date:</span>{' '}
                            {new Date(subscription.current_period_end).toLocaleDateString()}
                        </p>
                    )}
                    {subscription.cancel_at_period_end && (
                        <div className="bg-yellow-50 text-yellow-800 p-4 rounded-md mt-4">
                            Your subscription will end on {new Date(subscription.current_period_end!).toLocaleDateString()}
                        </div>
                    )}
                </div>

                <button
                    onClick={handleManageSubscription}
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                    {loading ? 'Loading...' : 'Manage Subscription'}
                </button>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-medium mb-2">Need Help?</h3>
                <p className="text-gray-600">
                    If you have any questions about your subscription, please contact our support team.
                </p>
            </div>
        </div>
    );
} 
