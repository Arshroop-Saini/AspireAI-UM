import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST(req: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.email || !session?.id_token) {
            console.error('Delete college: No session found');
            return NextResponse.json({ success: false, error: 'Not authenticated' }, { status: 401 });
        }

        const { college_name, source } = await req.json();
        console.log('Delete college request:', { college_name, source });
        
        if (!college_name || !source) {
            console.error('Delete college: Missing required fields');
            return NextResponse.json({
                success: false,
                error: 'Missing required fields: college_name or source'
            }, { status: 400 });
        }

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
        if (!backendUrl) {
            throw new Error('Backend URL not configured');
        }

        const deleteUrl = `${backendUrl}/api/college-list/delete-college`;
        console.log('Making request to:', deleteUrl);

        const response = await fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`
            },
            body: JSON.stringify({
                college_name,
                source
            })
        });

        console.log('Backend response status:', response.status);
        const data = await response.json();
        console.log('Backend response data:', data);

        if (!response.ok) {
            throw new Error(data.error || `Failed to delete college: ${response.status}`);
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Error in delete-college route:', error);
        return NextResponse.json({
            success: false,
            error: error instanceof Error ? error.message : 'Failed to delete college'
        }, { status: 500 });
    }
} 
