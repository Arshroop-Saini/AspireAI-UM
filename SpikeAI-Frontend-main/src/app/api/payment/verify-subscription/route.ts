import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function GET(req: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const { searchParams } = new URL(req.url);
        const sessionId = searchParams.get('session_id');
        
        if (!sessionId) {
            return NextResponse.json({ error: 'No session ID provided' }, { status: 400 });
        }

        const response = await fetch(
            `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/verify-subscription?session_id=${sessionId}`,
            {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${session.id_token}`,
                    'Content-Type': 'application/json'
                }
            }
        );

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to verify subscription');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Subscription verification error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to verify subscription' },
            { status: 500 }
        );
    }
} 