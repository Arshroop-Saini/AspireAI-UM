import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

// Protected routes that require authentication
const protectedRoutes = [
    '/dashboard',
    '/profile',
    '/college-list',
    '/ec-suggestions',
    '/essay-feedback',
    '/essay-brainstorm',
    '/settings',
    '/subscription'
];

// Protected API routes that require authentication
const protectedApiRoutes = [
    '/api/college-list',
    '/api/ec-suggestions',
    '/api/essay-feedback',
    '/api/essay-brainstorm',
    '/api/profile',
    '/api/payment'
];

export async function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Skip middleware for webhook routes and public assets
    if (pathname.startsWith('/api/webhooks') || 
        pathname.startsWith('/_next') || 
        pathname.startsWith('/fonts') || 
        pathname.startsWith('/examples') ||
        pathname === '/auth/signin' ||
        pathname === '/auth/error' ||
        pathname === '/auth/signout' ||
        pathname === '/') {
        return NextResponse.next();
    }

    // Get the token and create the base response
    const token = await getToken({ req: request });
    const response = NextResponse.next();

    // Add security headers
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('Referrer-Policy', 'origin-when-cross-origin');

    // Check if the route requires authentication
    const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
    const isProtectedApiRoute = protectedApiRoutes.some(route => pathname.startsWith(route));

    if (isProtectedRoute || isProtectedApiRoute) {
        if (!token) {
            // For API routes, return 401
            if (isProtectedApiRoute) {
                return NextResponse.json(
                    { error: 'Authentication required' },
                    { status: 401 }
                );
            }

            // For page routes, redirect to sign in
            const signInUrl = new URL('/auth/signin', request.url);
            signInUrl.searchParams.set('callbackUrl', pathname);
            return NextResponse.redirect(signInUrl);
        }

        // For protected routes that require subscription
        if (pathname.startsWith('/essay-feedback') || 
            pathname.startsWith('/essay-brainstorm') ||
            pathname.startsWith('/college-list') ||
            pathname.startsWith('/ec-suggestions')) {
            try {
                const subscriptionRes = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/verify-subscription`, {
                    headers: {
                        'Authorization': `Bearer ${token.access_token}`
                    }
                });

                if (!subscriptionRes.ok) {
                    // For API routes, return 403
                    if (isProtectedApiRoute) {
                        return NextResponse.json(
                            { error: 'Subscription required for this feature' },
                            { status: 403 }
                        );
                    }

                    // For page routes, redirect to subscription page
                    const subscriptionUrl = new URL('/subscription', request.url);
                    return NextResponse.redirect(subscriptionUrl);
                }
            } catch (error) {
                console.error('Subscription check error:', error);
                if (isProtectedApiRoute) {
                    return NextResponse.json(
                        { error: 'Failed to verify subscription status' },
                        { status: 500 }
                    );
                }
            }
        }
    }
    
    return response;
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones we explicitly skip
         * 1. /api/webhooks (webhook requests)
         * 2. /_next (Next.js internals)
         * 3. /fonts (static files)
         * 4. /examples (static files)
         * 5. all root files inside public (robots.txt, favicon.ico, etc.)
         */
        '/((?!api/webhooks|_next|fonts|examples|[\\w-]+\\.\\w+).*)',
    ],
}; 