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

        // Map source correctly
        const mappedSource = source === 'current' ? 'temp' : 'permanent';

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/ec-recommendation/add-target`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                activity_name: activity.name,
                activity_data: {
                    name: activity.name,
                    description: activity.description || '',
                    hours_per_week: activity.hours_per_week || 0,
                    activity_type: activity.activity_type || 'Other',
                    position: activity.position || '',
                    added_at: new Date().toISOString()
                },
                source: mappedSource
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to add activity to target list');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Add target activity error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to add activity to target list' },
            { status: 500 }
        );
    }
} 