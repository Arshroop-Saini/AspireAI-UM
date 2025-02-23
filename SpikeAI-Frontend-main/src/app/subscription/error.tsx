'use client';

import { useEffect } from 'react';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('Subscription error:', error);
    }, [error]);

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
            <div className="max-w-md w-full space-y-8 text-center">
                <div>
                    <h2 className="mt-6 text-3xl font-bold text-gray-900">
                        Something went wrong!
                    </h2>
                    <p className="mt-2 text-sm text-gray-600">
                        {error.message || 'Failed to load subscription plans. Please try again.'}
                    </p>
                </div>
                <div>
                    <button
                        onClick={reset}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Try again
                    </button>
                </div>
            </div>
        </div>
    );
} 
