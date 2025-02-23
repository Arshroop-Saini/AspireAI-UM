import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function GET(request: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.email || !session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        // Get page from URL params
        const { searchParams } = new URL(request.url);
        const page = searchParams.get('page') || '1';

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/ec-recommendation/target-activities?page=${page}`, {
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch target activities');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Target activities fetch error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to fetch target activities' },
            { status: 500 }
        );
    }
} 