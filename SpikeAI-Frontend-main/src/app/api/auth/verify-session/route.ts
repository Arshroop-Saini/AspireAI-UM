import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

interface UserData {
    email: string;
    name: string;
    picture: string;
}

interface CacheEntry {
    verified: boolean;
    user: UserData;
    timestamp: number;
}

// Cache verification results for 5 minutes
const CACHE_DURATION = 5 * 60 * 1000;
const verificationCache = new Map<string, CacheEntry>();

export async function GET(request: Request) {
    try {
        const session = await getServerSession(authOptions);
        if (!session?.id_token) {
            return NextResponse.json({ 
                success: false, 
                error: "Unauthorized" 
            }, { status: 401 });
        }

        // Check if this request is part of an ongoing generation
        const isGenerating = request.headers.get('X-Generation-In-Progress') === 'true';
        
        // Check cache first
        const cacheKey = session.user?.email || '';
        const cachedVerification = verificationCache.get(cacheKey);
        const now = Date.now();

        // If we're generating and have a cached verification, return it immediately
        if (isGenerating && cachedVerification) {
            console.log('Generation in progress - using cached verification');
            return NextResponse.json({
                success: true,
                user: cachedVerification.user
            });
        }

        // For non-generation requests, use normal cache expiry
        if (cachedVerification && (now - cachedVerification.timestamp) < CACHE_DURATION) {
            console.log('Returning cached verification result');
            return NextResponse.json({
                success: true,
                user: cachedVerification.user
            });
        }

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
        if (!backendUrl) {
            throw new Error('Backend URL not configured');
        }

        console.log('Cache miss - verifying session with backend');
        const response = await fetch(`${backendUrl}/api/auth/verify-session`, {
            headers: {
                'Authorization': `Bearer ${session.id_token}`
            }
        });

        const data = await response.json();

        // Cache successful verifications
        if (data.success) {
            verificationCache.set(cacheKey, {
                verified: true,
                user: data.user,
                timestamp: now
            });
        }

        return NextResponse.json(data);

    } catch (error) {
        console.error('Session verification error:', error);
        return NextResponse.json({ 
            success: false,
            error: error instanceof Error ? error.message : 'Failed to verify session'
        }, { status: 500 });
    }
} 