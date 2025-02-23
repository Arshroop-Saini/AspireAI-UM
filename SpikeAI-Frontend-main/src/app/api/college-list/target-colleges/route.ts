import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function GET(request: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        // Get page from URL parameters
        const url = new URL(request.url);
        const page = url.searchParams.get('page') || '1';
        const per_page = url.searchParams.get('per_page') || '10';

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/college-list/target-colleges?page=${page}&per_page=${per_page}`, {
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch target colleges');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Target colleges fetch error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to fetch target colleges' },
            { status: 500 }
        );
    }
} 