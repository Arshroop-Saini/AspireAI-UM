import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';

interface SubscriptionGuardProps {
    children: React.ReactNode;
    feature?: string;
}

interface SubscriptionStatus {
    is_subscribed: boolean;
    plan: string | null;
    status: string;
    features: string[];
}

export default function SubscriptionGuard({ children, feature }: SubscriptionGuardProps) {
    const { data: session } = useSession();
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [hasAccess, setHasAccess] = useState(false);

    useEffect(() => {
        const checkSubscription = async () => {
            try {
                const response = await fetch('/api/subscription');
                if (!response.ok) {
                    throw new Error('Failed to fetch subscription status');
                }

                const data: SubscriptionStatus = await response.json();
                
                if (!feature) {
                    // If no specific feature is required, just check if subscribed
                    setHasAccess(data.is_subscribed && data.status === 'active');
                } else {
                    // Check if user has access to the specific feature
                    setHasAccess(
                        data.is_subscribed && 
                        data.status === 'active' && 
                        data.features.includes(feature)
                    );
                }
            } catch (error) {
                console.error('Error checking subscription:', error);
                setHasAccess(false);
            } finally {
                setLoading(false);
            }
        };

        if (session) {
            checkSubscription();
        } else {
            setLoading(false);
            setHasAccess(false);
        }
    }, [session, feature]);

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-[200px]">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (!hasAccess) {
        return (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                <h3 className="text-lg font-semibold text-yellow-800 mb-2">
                    Premium Feature
                </h3>
                <p className="text-yellow-700 mb-4">
                    {feature
                        ? `This feature requires a subscription with ${feature} access.`
                        : 'This feature requires an active subscription.'}
                </p>
                <button
                    onClick={() => router.push('/subscription')}
                    className="bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-2 px-4 rounded transition-colors"
                >
                    View Subscription Plans
                </button>
            </div>
        );
    }

    return <>{children}</>;
} 
