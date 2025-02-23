import { NextResponse } from 'next/server';

export async function GET() {
    try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/payment/prices`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch prices');
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error fetching prices:', error);
        return NextResponse.json(
            { error: 'Failed to fetch subscription prices' },
            { status: 500 }
        );
    }
} 