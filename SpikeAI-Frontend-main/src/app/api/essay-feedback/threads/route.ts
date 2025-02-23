import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { v4 as uuidv4 } from 'uuid';

// GET /api/essay-feedback/threads - List all threads
export async function GET() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.sub || !session?.id_token) {
            return NextResponse.json(
                { error: 'Authentication required' },
                { status: 401 }
            );
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/essay-feedback/threads`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`
            }
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Failed to fetch essay feedback threads');
        }

        const result = await response.json();
        return NextResponse.json(result);
    } catch (error) {
        console.error('Error fetching essay feedback threads:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to fetch essay feedback threads' },
            { status: 500 }
        );
    }
}

// POST /api/essay-feedback/threads - Create a new thread
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
        const { college_name, prompt, essay_text, word_count, feedback_questions } = data;

        // Validate required fields
        if (!college_name || !prompt || !essay_text || !word_count) {
            return NextResponse.json(
                { error: 'Missing required fields' },
                { status: 400 }
            );
        }

        const thread_data = {
            thread_id: uuidv4(), // Generate unique thread ID
            college_name,
            prompt,
            essay_text,
            word_count,
            feedback_questions: feedback_questions || []
        };

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/essay-feedback/threads`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`
            },
            body: JSON.stringify(thread_data),
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Failed to create essay feedback thread');
        }

        const result = await response.json();
        return NextResponse.json(result);
    } catch (error) {
        console.error('Error creating essay feedback thread:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to create essay feedback thread' },
            { status: 500 }
        );
    }
}

// DELETE /api/essay-feedback/threads/[threadId] - Delete a thread
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

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/essay-feedback/threads/${threadId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`
            }
        });

        if (!response.ok) {
            const result = await response.json();
            throw new Error(result.error || 'Failed to delete essay feedback thread');
        }

        return new NextResponse(null, { status: 204 });
    } catch (error) {
        console.error('Error deleting essay feedback thread:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to delete essay feedback thread' },
            { status: 500 }
        );
    }
} 