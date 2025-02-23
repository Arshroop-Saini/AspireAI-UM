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
            console.error('Authentication failed: Missing email or id_token in session');
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        // Get auth0_id from session
        const auth0_id = session.user.sub;
        if (!auth0_id) {
            console.error('Authentication failed: Missing auth0_id in session');
            return NextResponse.json({ error: 'Auth0 ID not found in session' }, { status: 401 });
        }

        // Parse request body to get activity type and hours per week
        const body = await request.json();
        const { activity_type, hrs_per_wk } = body;

        if (!activity_type || !hrs_per_wk) {
            console.error('Validation failed: Missing activity_type or hrs_per_wk in request body');
            return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
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

        console.log('Making request to backend:', {
            url: `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/ec-recommendation/`,
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            },
            body: {
                activity_type,
                hrs_per_wk
            }
        });

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/ec-recommendation/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                activity_type,
                hrs_per_wk
            })
        });

        // Log the raw response for debugging
        console.log('Backend response status:', response.status);
        console.log('Backend response headers:', Object.fromEntries(response.headers.entries()));
        
        const data = await response.json().catch(e => {
            console.error('Failed to parse response as JSON:', e);
            throw new Error('Invalid JSON response from server');
        });
        
        console.log('Backend response data:', data);
        
        if (!response.ok) {
            throw new Error(data.error || `Server responded with status ${response.status}`);
        }

        // Clear generation in progress
        activeGenerations.delete(auth0_id);

        return NextResponse.json(data);
    } catch (error) {
        console.error('EC suggestions generation error:', error);
        // Clear generation in progress on error
        if (session?.user?.sub) {
            activeGenerations.delete(session.user.sub);
        }
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to generate EC suggestions' },
            { status: 500 }
        );
    }
} 