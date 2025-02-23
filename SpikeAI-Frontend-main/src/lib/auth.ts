import { NextAuthOptions, Session, DefaultSession } from "next-auth";
import GoogleProvider from "next-auth/providers/google";

declare module "next-auth" {
    interface Session {
        access_token?: string;
        id_token?: string;
        user?: {
            email?: string | null;
            name?: string | null;
            image?: string | null;
            sub?: string | null;
        }
        error?: string;
    }

    interface JWT {
        access_token?: string;
        id_token?: string;
        email?: string;
        name?: string;
        picture?: string;
        sub?: string;
        error?: string;
    }
}

export const authOptions: NextAuthOptions = {
    providers: [
        GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID!,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
            authorization: {
                params: {
                    access_type: "offline",
                    prompt: "consent",
                    response_type: "code",
                    scope: "openid email profile"
                }
            }
        })
    ],
    secret: process.env.NEXTAUTH_SECRET,
    session: {
        strategy: 'jwt',
        maxAge: 12 * 60 * 60, // 12 hours
        updateAge: 1 * 60 * 60 // 1 hour
    },
    callbacks: {
        async signIn({ user, account }) {
            if (account?.id_token) {
                try {
                    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/profile/sync-user`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${account.id_token}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            email: user.email,
                            name: user.name,
                            picture: user.image
                        })
                    });

                    if (!response.ok) {
                        console.error('Failed to sync user with database');
                        return true; // Still allow sign in even if sync fails
                    }

                    const data = await response.json();
                    if (!data.success) {
                        console.error('User sync failed:', data.error);
                        return true; // Still allow sign in even if sync fails
                    }

                    return true;
                } catch (error) {
                    console.error('Error syncing user:', error);
                    return true; // Still allow sign in even if sync fails
                }
            }
            return true;
        },
        async jwt({ token, account, trigger, session }) {
            // Initial sign in
            if (account) {
                token.access_token = account.access_token;
                token.id_token = account.id_token;
                return token;
            }

            // Handle token updates
            if (trigger === "update" && session) {
                token = { ...token, ...session };
                return token;
            }

            // Check token expiration
            const tokenExpiration = (token.exp as number) * 1000;
            if (Date.now() > tokenExpiration) {
                token.error = "TokenExpired";
                return token;
            }

            return token;
        },
        async session({ session, token }): Promise<Session | DefaultSession> {
            if (token) {
                // Pass the error to the session if present
                if (token.error) {
                    session.error = token.error;
                }

                session.access_token = token.access_token as string;
                session.id_token = token.id_token as string;
                if (session.user) {
                    session.user.email = token.email as string;
                    session.user.name = token.name as string;
                    session.user.image = token.picture as string;
                    session.user.sub = token.sub as string;
                }
            }
            return session;
        }
    },
    events: {
        async signOut({ session, token }) {
            if (session?.id_token) {
                try {
                    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/auth/signout`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${session.id_token}`
                        }
                    });

                    if (!response.ok) {
                        console.error('Failed to sign out from backend');
                    }
                } catch (error) {
                    console.error('Error signing out:', error);
                }
            }
        }
    },
    pages: {
        signIn: '/auth/signin',
        error: '/auth/error',
        signOut: '/auth/signout'
    },
    debug: process.env.NODE_ENV === 'development'
};