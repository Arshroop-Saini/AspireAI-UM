import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST(req: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.email || !session?.id_token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { subscription_type } = await req.json();
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/create-subscription`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`,
                'Accept': 'application/json'
            },
            body: JSON.stringify({ subscription_type })
        });

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Expected JSON response but got ' + contentType);
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to create subscription');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Subscription error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to process subscription' },
            { status: 500 }
        );
    }
}

export async function GET() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.email || !session?.id_token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/subscription-status`, {
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Accept': 'application/json'
            }
        });

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Expected JSON response but got ' + contentType);
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch subscription status');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Error fetching subscription status:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to fetch subscription status' },
            { status: 500 }
        );
    }
}

export async function DELETE() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.email || !session?.id_token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/cancel-subscription`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.id_token}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            console.error('Subscription cancellation error:', data);
            throw new Error(data.error || 'Failed to cancel subscription');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Error canceling subscription:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to cancel subscription' },
            { status: 500 }
        );
    }
} 