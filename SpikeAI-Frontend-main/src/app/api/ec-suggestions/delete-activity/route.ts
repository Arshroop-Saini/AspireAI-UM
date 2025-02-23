import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST(request: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.email || !session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const body = await request.json();
        const { activity, source } = body;

        if (!activity || !source) {
            return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
        }

        // Map source correctly for the backend
        let mappedSource;
        if (source === 'current') {
            mappedSource = 'current';
        } else if (source === 'past') {
            mappedSource = 'past';
        } else if (source === 'target') {
            mappedSource = 'target';
        } else {
            return NextResponse.json({ error: 'Invalid source' }, { status: 400 });
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/ec-recommendation/delete-activity`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                activity_name: activity.name,
                source: mappedSource
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete activity');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Delete activity error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to delete activity' },
            { status: 500 }
        );
    }
} 