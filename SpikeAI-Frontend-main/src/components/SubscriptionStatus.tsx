'use client';

import { useEffect, useState } from 'react';

interface SubscriptionDetails {
    is_subscribed: boolean;
    status: string;
    plan_type?: string;
    current_period_end?: string;
}

export function SubscriptionStatus() {
    const [subscription, setSubscription] = useState<SubscriptionDetails | null>(null);

    useEffect(() => {
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

        fetchSubscriptionStatus();
    }, []);

    if (!subscription) return null;

    return (
        <div className="bg-gray-900 rounded-lg p-4 text-white mb-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                        subscription.status === 'active' ? 'bg-green-400' : 'bg-yellow-400'
                    }`} />
                    <span className="font-medium">
                        {subscription.is_subscribed ? 'Premium Plan' : 'Free Plan'}
                    </span>
                </div>
                {subscription.is_subscribed && (
                    <span className="text-sm text-gray-400">
                        Next billing: {new Date(subscription.current_period_end!).toLocaleDateString()}
                    </span>
                )}
            </div>
        </div>
    );
} 
