import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function GET() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ 
                success: false,
                error: 'Not authenticated',
                subscription: {
                    is_subscribed: false,
                    status: 'inactive',
                    features: []
                }
            }, { status: 401 });
        }

        console.log('Fetching subscription status from:', `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/subscription-status`);
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/subscription-status`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Accept': 'application/json'
            }
        });

        console.log('Backend response status:', response.status);
        const data = await response.json();
        console.log('Backend response data:', data);

        if (!response.ok) {
            console.error('Backend subscription error:', data);
            return NextResponse.json({ 
                success: false,
                error: data.error || 'Failed to fetch subscription status',
                subscription: {
                    is_subscribed: false,
                    status: 'inactive',
                    features: []
                }
            }, { status: response.status });
        }

        return NextResponse.json({
            success: true,
            subscription: data.subscription
        });
    } catch (error) {
        console.error('Error fetching subscription status:', error);
        return NextResponse.json({ 
            success: false,
            error: error instanceof Error ? error.message : 'Failed to fetch subscription status',
            subscription: {
                is_subscribed: false,
                status: 'inactive',
                features: []
            }
        }, { status: 500 });
    }
} 