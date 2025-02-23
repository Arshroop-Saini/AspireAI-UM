import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST(request: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const body = await request.json();
        const { college_name, source } = body;

        if (!college_name || !source) {
            return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/college-list/add-target`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ college_name, source })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to add college to target list');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Add target college error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to add college to target list' },
            { status: 500 }
        );
    }
} 