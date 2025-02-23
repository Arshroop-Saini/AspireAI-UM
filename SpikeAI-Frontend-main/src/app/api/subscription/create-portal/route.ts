import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/create-portal-session`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        const data = await response.json();

        if (!response.ok) {
            console.error('Portal session error:', data);
            throw new Error(data.error || 'Failed to create portal session');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Portal session error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to create portal session' },
            { status: 500 }
        );
    }
} 