import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

interface ProfileData {
    success: boolean;
    profile: {
        _id?: string;
        email: string;
        name: string;
        [key: string]: any; // Allow other profile fields
    };
}

interface CacheEntry {
    data: ProfileData;
    timestamp: number;
}

// Cache profile data for 30 seconds
const CACHE_DURATION = 30 * 1000; // 30 seconds
const profileCache = new Map<string, CacheEntry>();

export async function GET() {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ 
                success: false, 
                error: "Unauthorized" 
            }, { status: 401 });
        }

        // Check cache first
        const cacheKey = session.user?.email || '';
        const cachedData = profileCache.get(cacheKey);
        const now = Date.now();

        if (cachedData && (now - cachedData.timestamp) < CACHE_DURATION) {
            console.log('Returning cached profile data');
            return NextResponse.json(cachedData.data);
        }

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
        if (!backendUrl) {
            throw new Error('Backend URL not configured');
        }

        console.log('Cache miss - fetching fresh profile data');
        const response = await fetch(`${backendUrl}/api/profile/`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${session.id_token}`
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend error response:', errorText);
            try {
                const errorData = JSON.parse(errorText);
                return NextResponse.json({ 
                    success: false,
                    error: errorData.error || 'Failed to fetch profile'
                }, { status: response.status });
            } catch {
                return NextResponse.json({ 
                    success: false,
                    error: errorText || 'Failed to fetch profile'
                }, { status: response.status });
            }
        }

        const data = await response.json();

        if (!data.success || !data.profile) {
            console.error('Invalid profile data:', data);
            return NextResponse.json({ 
                success: false,
                error: 'Invalid profile data received'
            }, { status: 400 });
        }

        // Cache the successful response
        const responseData = {
            success: true,
            profile: data.profile
        };
        profileCache.set(cacheKey, { data: responseData, timestamp: now });

        return NextResponse.json(responseData);

    } catch (error) {
        console.error('Profile fetch error:', error);
        return NextResponse.json({ 
            success: false,
            error: error instanceof Error ? error.message : 'Failed to fetch profile'
        }, { status: 500 });
    }
}

// Clear cache when profile is updated
export async function PUT(req: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return Response.json({ 
                success: false, 
                error: 'Not authenticated' 
            }, { status: 401 });
        }

        // Clear the cache for this user
        const cacheKey = session.user?.email || '';
        profileCache.delete(cacheKey);

        const data = await req.json();
        console.log('Updating profile with data:', data);

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
        if (!backendUrl) {
            throw new Error('Backend URL not configured');
        }

        const response = await fetch(`${backendUrl}/api/profile`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const responseText = await response.text();
        console.log('Backend response:', responseText);

        let responseData;
        try {
            responseData = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse backend response:', e);
            return Response.json({
                success: false,
                error: 'Invalid response from server'
            }, { status: 500 });
        }

        return Response.json(responseData);
    } catch (error) {
        console.error('Error updating profile:', error);
        return Response.json({
            success: false,
            error: error instanceof Error ? error.message : 'Failed to update profile'
        }, { status: 500 });
    }
}