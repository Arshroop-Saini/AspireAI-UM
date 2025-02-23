import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function DELETE() {
    try {
        // Get session to verify user is authenticated
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
        if (!backendUrl) {
            throw new Error('Backend URL not configured');
        }

        // Forward the request to the backend with the Google token
        const response = await fetch(`${backendUrl}/api/profile`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        const data = await response.json();
        console.log('Backend delete response:', data);

        if (!response.ok) {
            console.error('Delete profile error:', data);
            return NextResponse.json(
                { error: data.error || 'Failed to delete profile' }, 
                { status: response.status }
            );
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Error deleting profile:', error);
        return NextResponse.json(
            { error: 'Internal server error' }, 
            { status: 500 }
        );
    }
} 