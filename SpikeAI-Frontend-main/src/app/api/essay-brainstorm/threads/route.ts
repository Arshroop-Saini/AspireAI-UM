import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { v4 as uuidv4 } from 'uuid';

// GET /api/essay-brainstorm/threads - List all threads
export async function GET() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.sub || !session?.id_token) {
            return NextResponse.json(
                { error: 'Authentication required' },
                { status: 401 }
            );
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/essay-brainstorm/threads`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch threads');
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Error fetching threads:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to fetch threads' },
            { status: 500 }
        );
    }
}

// POST /api/essay-brainstorm/threads - Create a new thread
export async function POST(req: NextRequest) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.sub || !session?.id_token) {
            return NextResponse.json(
                { error: 'Authentication required' },
                { status: 401 }
            );
        }

        const data = await req.json();
        const { college_name, essay_prompt, word_limit } = data;

        // Validate required fields
        if (!college_name || !essay_prompt) {
            return NextResponse.json(
                { error: 'Missing required fields' },
                { status: 400 }
            );
        }

        const thread_data = {
            thread_id: uuidv4(), // Generate unique thread ID
            college_name,
            essay_prompt,
            word_limit: Number(word_limit) || 0
        };

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/essay-brainstorm/threads`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`
            },
            body: JSON.stringify(thread_data),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to create essay brainstorm thread');
        }

        return NextResponse.json({
            success: true,
            thread_id: thread_data.thread_id,
            ...result
        });
    } catch (error) {
        console.error('Error creating essay brainstorm thread:', error);
        return NextResponse.json(
            { 
                success: false,
                error: error instanceof Error ? error.message : 'Failed to create essay brainstorm thread' 
            },
            { status: 500 }
        );
    }
}

export async function DELETE(req: NextRequest) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.sub || !session?.id_token) {
            return NextResponse.json(
                { error: 'Authentication required' },
                { status: 401 }
            );
        }

        const url = new URL(req.url);
        const threadId = url.searchParams.get('threadId');

        if (!threadId) {
            return NextResponse.json(
                { error: 'Thread ID is required' },
                { status: 400 }
            );
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/essay-brainstorm/threads/${threadId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`
            }
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({ error: 'Failed to delete thread' }));
            throw new Error(data.error || 'Failed to delete thread');
        }

        return new NextResponse(null, { status: 204 });
    } catch (error) {
        console.error('Error deleting thread:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to delete thread' },
            { status: 500 }
        );
    }
} 