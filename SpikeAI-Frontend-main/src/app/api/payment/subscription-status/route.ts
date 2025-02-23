import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { NextResponse } from "next/server";

export async function GET() {
    try {
        const session = await getServerSession(authOptions);
        
        if (!session?.id_token) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
        if (!backendUrl) {
            throw new Error('Backend URL not configured');
        }

        const response = await fetch(`${backendUrl}/api/payment/subscription-status`, {
            headers: {
                'Authorization': `Bearer ${session.id_token}`,
                'Content-Type': 'application/json'
            },
            cache: 'no-store'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch subscription status');
        }

        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('Subscription status error:', error);
        return NextResponse.json({ 
            error: 'Failed to fetch subscription status',
            details: error instanceof Error ? error.message : String(error)
        }, { status: 500 });
    }
} 