import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';

interface SubscriptionStatus {
    isSubscribed: boolean;
    isLoading: boolean;
    error: string | null;
}

export function useSubscriptionStatus(): SubscriptionStatus {
    const { data: session, status } = useSession();
    const [isSubscribed, setIsSubscribed] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function checkSubscription() {
            if (status === 'loading' || !session?.id_token) {
                return;
            }

            try {
                const response = await fetch('/api/profile', {
                    headers: {
                        'Authorization': `Bearer ${session.id_token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch profile');
                }

                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error || 'Failed to fetch profile');
                }

                // Check if user has an active subscription
                const subscription = data.profile?.subscription;
                setIsSubscribed(subscription?.is_subscribed || false);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to check subscription');
                // Don't set isSubscribed to false on error - maintain current state
            } finally {
                setIsLoading(false);
            }
        }

        checkSubscription();
    }, [session, status]);

    return { isSubscribed, isLoading, error };
} 