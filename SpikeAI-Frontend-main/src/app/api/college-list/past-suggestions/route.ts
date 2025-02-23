import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function GET() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/college-list/past-suggestions`, {
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch past suggestions');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Past suggestions fetch error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to fetch past suggestions' },
            { status: 500 }
        );
    }
} 