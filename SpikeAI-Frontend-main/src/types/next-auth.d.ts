import 'next-auth';

declare module 'next-auth' {
    interface Session {
        access_token?: string;
        id_token?: string;
        user?: {
            email?: string | null;
            name?: string | null;
            image?: string | null;
        }
    }
} 