import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.email || !session?.access_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/create-stripe-session`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.access_token}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to create Stripe session');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Stripe session error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to create Stripe session' },
            { status: 500 }
        );
    }
} 