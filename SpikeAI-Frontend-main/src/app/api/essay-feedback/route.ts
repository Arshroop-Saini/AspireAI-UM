import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST(req: NextRequest) {
    try {
        const session = await getServerSession(authOptions);
        
        if (!session?.user) {
            return NextResponse.json(
                { error: 'Authentication required' },
                { status: 401 }
            );
        }

        const data = await req.json();
        const { college_name, prompt, essay_text, word_count, feedback_questions, is_new_thread, thread_id } = data;

        // Validate required fields
        if (!college_name || !prompt || !essay_text || !word_count) {
            return NextResponse.json(
                { error: 'Missing required fields' },
                { status: 400 }
            );
        }

        // Make request to backend API
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/essay-feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.id_token}`
            },
            body: JSON.stringify({
                college_name,
                prompt,
                essay_text,
                word_count,
                feedback_questions: feedback_questions || [],
                is_new_thread,
                thread_id,
                auth0_id: session.user.sub
            }),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to get essay feedback');
        }

        return NextResponse.json(result);
    } catch (error) {
        console.error('Essay feedback error:', error);
        return NextResponse.json(
            { error: 'Failed to process essay feedback request' },
            { status: 500 }
        );
    }
} 