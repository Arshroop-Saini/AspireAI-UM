'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface FeaturePageProps {
    title: string;
    description: string;
    endpoint: string;
    buttonText: string;
    showCollegeTypeDropdown?: boolean;
}

export function FeaturePage({ title, description, endpoint, buttonText, showCollegeTypeDropdown }: FeaturePageProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<any>(null);
    const [collegeType, setCollegeType] = useState<string>('target');
    const router = useRouter();
    const abortControllerRef = useRef<AbortController | null>(null);

    const handleFeatureRequest = async () => {
        try {
            setLoading(true);
            setError(null);
            setResult(null);

            // Create new AbortController for this request
            abortControllerRef.current = new AbortController();

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    requestType: 'generate',
                    collegeType: collegeType
                }),
                signal: abortControllerRef.current.signal
            });

            if (!response.ok) {
                const error = await response.json();
                if (response.status === 401) {
                    router.push('/login');
                    return;
                }
                if (response.status === 403) {
                    router.push('/settings');
                    return;
                }
                throw new Error(error.message || 'Failed to process request');
            }

            const data = await response.json();
            setResult(data);

        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                setError('Request cancelled');
            } else {
                setError(error instanceof Error ? error.message : 'An error occurred');
            }
        } finally {
            setLoading(false);
            abortControllerRef.current = null;
        }
    };

    const handleCancel = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white py-12">
            <div className="max-w-4xl mx-auto px-4">
                <h1 className="text-3xl font-bold mb-4">{title}</h1>
                <p className="text-gray-400 mb-8">{description}</p>

                {showCollegeTypeDropdown && (
                    <div className="mb-6">
                        <label htmlFor="collegeType" className="block text-sm font-medium text-gray-300 mb-2">
                            Select College Type
                        </label>
                        <select
                            id="collegeType"
                            value={collegeType}
                            onChange={(e) => setCollegeType(e.target.value)}
                            className="bg-gray-800 text-white rounded-lg px-4 py-2 w-full max-w-xs"
                        >
                            <option value="target">Target Schools</option>
                            <option value="reach">Reach Schools</option>
                            <option value="safety">Safety Schools</option>
                        </select>
                    </div>
                )}

                {error && (
                    <div className="bg-red-900/50 text-red-200 p-4 rounded-lg mb-6">
                        {error}
                    </div>
                )}

                <div className="flex gap-4 mb-8">
                    <button
                        onClick={handleFeatureRequest}
                        disabled={loading}
                        className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 
                                 disabled:opacity-50 transition-colors duration-200"
                    >
                        {loading ? 'Processing...' : buttonText}
                    </button>

                    {loading && (
                        <button
                            onClick={handleCancel}
                            className="bg-red-600 text-white px-8 py-3 rounded-lg hover:bg-red-700 
                                     transition-colors duration-200"
                        >
                            Cancel Request
                        </button>
                    )}
                </div>

                {result && (
                    <div className="bg-gray-800 rounded-lg p-6 mt-8 border border-gray-700">
                        <h2 className="text-xl font-semibold mb-4">Results</h2>
                        <pre className="whitespace-pre-wrap text-gray-300 font-mono text-sm">
                            {JSON.stringify(result, null, 2)}
                        </pre>
                    </div>
                )}
            </div>
        </div>
    );
} 
