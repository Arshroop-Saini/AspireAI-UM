import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";
import { authOptions } from "@/lib/auth";

export async function POST() {
    try {
        const session = await getServerSession(authOptions);
        
        if (!session?.id_token) {
            return NextResponse.json(
                { success: false, error: "Not authenticated" },
                { status: 401 }
            );
        }

        const response = await fetch(
            `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/create-portal-session`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${session.id_token}`,
                    Accept: "application/json",
                },
            }
        );

        const data = await response.json();

        if (!response.ok) {
            console.error("Portal session error:", data);
            return NextResponse.json(
                { success: false, error: data.error || "Failed to create portal session" },
                { status: response.status }
            );
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error("Error creating portal session:", error);
        return NextResponse.json(
            { success: false, error: "Internal server error" },
            { status: 500 }
        );
    }
} 