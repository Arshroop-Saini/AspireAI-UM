import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

// Keep track of ongoing generations
const activeGenerations = new Map<string, boolean>();

export async function POST(request: Request) {
    let session;
    try {
        session = await getServerSession(authOptions);
        if (!session?.user?.email || !session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        // Get auth0_id from session
        const auth0_id = session.user.sub;
        if (!auth0_id) {
            return NextResponse.json({ error: 'Auth0 ID not found in session' }, { status: 401 });
        }

        // Parse request body to get the type
        const body = await request.json();
        const { type } = body;
        if (!type || !['safety', 'target', 'reach'].includes(type)) {
            return NextResponse.json({ error: 'Invalid college type' }, { status: 400 });
        }

        // Check if generation is already in progress for this user
        if (activeGenerations.get(auth0_id)) {
            return NextResponse.json({ 
                success: true, 
                message: 'Generation in progress' 
            });
        }

        // Set generation in progress
        activeGenerations.set(auth0_id, true);

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/college-list/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                auth0_id: auth0_id,
                college_type: type
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate college list');
        }

        // Clear generation in progress
        activeGenerations.delete(auth0_id);

        return NextResponse.json(data);
    } catch (error) {
        console.error('College list generation error:', error);
        // Clear generation in progress on error
        if (session?.user?.sub) {
            activeGenerations.delete(session.user.sub);
        }
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to generate college list' },
            { status: 500 }
        );
    }
} 