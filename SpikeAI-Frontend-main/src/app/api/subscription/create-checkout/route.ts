import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST(req: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const { plan_type } = await req.json();
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/create-checkout`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`,
                'Accept': 'application/json'
            },
            body: JSON.stringify({ plan_type })
        });

        const data = await response.json();
        
        if (!response.ok) {
            console.error('Checkout error:', data);
            throw new Error(data.error || 'Failed to create checkout session');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Checkout error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to create checkout session' },
            { status: 500 }
        );
    }
} 