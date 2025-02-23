import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.access_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/essay-feedback/generate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.access_token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(error, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Essay feedback error:', error);
        return NextResponse.json(
            { error: 'Failed to generate essay feedback' },
            { status: 500 }
        );
    }
} 