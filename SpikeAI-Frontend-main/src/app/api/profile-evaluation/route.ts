import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST() {
    try {
        const session = await getServerSession(authOptions);
        
        if (!session?.user) {
            return NextResponse.json(
                { error: 'Authentication required' },
                { status: 401 }
            );
        }

        // Make request to backend API
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/profile-evaluation/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`
            }
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to evaluate profile');
        }

        return NextResponse.json(result);
    } catch (error) {
        console.error('Profile evaluation error:', error);
        return NextResponse.json(
            { error: 'Failed to process profile evaluation request' },
            { status: 500 }
        );
    }
} 