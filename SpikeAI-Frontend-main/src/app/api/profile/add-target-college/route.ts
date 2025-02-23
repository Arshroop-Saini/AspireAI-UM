import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function POST(request: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.user?.email || !session?.id_token) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const auth0_id = session.user.sub;
        if (!auth0_id) {
            return NextResponse.json({ error: 'Auth0 ID not found in session' }, { status: 401 });
        }

        const { collegeName } = await request.json();
        if (!collegeName) {
            return NextResponse.json({ error: 'College name is required' }, { status: 400 });
        }

        // First get the current profile to get existing target colleges
        const profileResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/profile`, {
            method: 'GET',  // Explicitly set method to GET
            headers: {
                'Authorization': `Bearer ${session.id_token}`
            }
        });

        if (!profileResponse.ok) {
            const errorData = await profileResponse.json().catch(() => ({}));
            throw new Error(errorData.error || 'Failed to fetch profile');
        }

        const profileData = await profileResponse.json();
        if (!profileData.success) {
            throw new Error(profileData.error || 'Failed to fetch profile');
        }

        // Get current target colleges and add the new one
        const currentTargetColleges = profileData.profile.target_colleges || [];
        if (currentTargetColleges.includes(collegeName)) {
            return NextResponse.json({ 
                error: 'College is already in your target list' 
            }, { status: 400 });
        }

        // Update profile with new target college
        const updateResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/profile`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_colleges: [...currentTargetColleges, collegeName]
            })
        });

        if (!updateResponse.ok) {
            const errorData = await updateResponse.json().catch(() => ({}));
            throw new Error(errorData.error || 'Failed to update target colleges');
        }

        const data = await updateResponse.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to update target colleges');
        }

        return NextResponse.json({
            success: true,
            data: {
                message: `${collegeName} added to target colleges`,
                target_colleges: data.profile.target_colleges
            }
        });
    } catch (error) {
        console.error('Error adding target college:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to add target college' },
            { status: 500 }
        );
    }
} 