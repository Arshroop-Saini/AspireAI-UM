import { NextResponse } from 'next/server';
import { getToken } from 'next-auth/jwt';
import { NextRequestWithAuth, withAuth } from 'next-auth/middleware';

// Protect these routes - require authentication
export const config = {
    matcher: [
        '/dashboard',
        '/profile',
        '/settings',
        '/college-list',
        '/essay-feedback',
        '/major-suggestions',
        '/theme-generator',
        '/ec-recommendations'
    ]
};

export default withAuth(
    async function middleware(req: NextRequestWithAuth) {
        const token = await getToken({ req });
        const isAuthenticated = !!token;

        if (!isAuthenticated) {
            const signinUrl = new URL('/auth/signin', req.url);
            return NextResponse.redirect(signinUrl);
        }

        return NextResponse.next();
    },
    {
        callbacks: {
            authorized: () => true // Let the above middleware handle the authentication
        }
    }
); 