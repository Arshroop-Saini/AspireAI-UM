'use client';

import { format } from 'date-fns';
import { NextFontWithVariable } from 'next/dist/compiled/@next/font';
import { RefreshCw } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

interface EvaluationScores {
    testing_score: number;
    hsr_score: number;
    ecs_score: number;
    spiv_score: number;
    eval_score: number;
    last_evaluated: string;
}

interface ProfileEvaluationMetersProps {
    scores: EvaluationScores;
    mono: NextFontWithVariable;
}

export default function ProfileEvaluationMeters({ scores, mono }: ProfileEvaluationMetersProps) {
    const { toast } = useToast();

    const handleEvaluateProfile = async () => {
        try {
            const response = await fetch('/api/profile-evaluation', {
                method: 'POST',
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to evaluate profile');
            }

            toast({
                title: 'Success',
                description: 'Profile evaluation completed',
            });

            // Refresh the page to get updated scores
            window.location.reload();
        } catch (error) {
            console.error('Profile evaluation error:', error);
            toast({
                title: 'Error',
                description: 'Failed to evaluate profile',
                variant: 'destructive',
            });
        }
    };

    const getRotation = (score: number) => {
        // Convert score (1-6) to degrees (0-180)
        const degrees = ((score - 1) / 5) * 180;
        return degrees - 90; // Adjust to start from the bottom
    };

    const renderMeter = (label: string, score: number) => {
        const rotation = getRotation(score);

        return (
            <div className="p-4 bg-[#1A1A1A] rounded-lg">
                <div className={`text-center mb-2 text-xs text-gray-400 ${mono.className}`}>{label}</div>
                <div className="relative w-28 h-28 mx-auto">
                    {/* Background Arc */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-full h-full rounded-full border-[3px] border-[#2A2A2A] opacity-50"></div>
                    </div>
                    
                    {/* Score Arc */}
                    <div 
                        className="absolute inset-0 flex items-center justify-center"
                        style={{
                            transform: `rotate(${rotation}deg)`,
                            transition: 'transform 1s ease-out'
                        }}
                    >
                        <div className="absolute top-0 left-1/2 h-1/2 origin-bottom">
                            <div className="w-0.5 h-full bg-[#E87C3E]"></div>
                        </div>
                    </div>
                    
                    {/* Score Numbers */}
                    <div className={`absolute bottom-0 left-0 text-[10px] text-gray-500 ${mono.className}`}>1</div>
                    <div className={`absolute bottom-0 right-0 text-[10px] text-gray-500 ${mono.className}`}>6</div>
                    
                    {/* Score Value */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className={`text-2xl text-[#E87C3E] ${mono.className}`}>{score.toFixed(1)}</div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="max-w-5xl mx-auto px-4 mt-8">
            <div className="grid grid-cols-5 gap-4 mb-8">
                {renderMeter('Testing\nScore', scores.testing_score)}
                {renderMeter('HSR\nScore', scores.hsr_score)}
                {renderMeter('ECs\nScore', scores.ecs_score)}
                {renderMeter('SPIV\nScore', scores.spiv_score)}
                {renderMeter('EVAL\nScore', scores.eval_score)}
            </div>
            <div className="flex flex-col items-center gap-4">
                <button 
                    onClick={handleEvaluateProfile}
                    className={`px-6 py-2 bg-[#E87C3E] text-white rounded-lg transition-all duration-200 hover:bg-[#FF8D4E] hover:shadow-lg hover:shadow-[#E87C3E]/20 flex items-center gap-2 ${mono.className}`}
                >
                    <RefreshCw className="h-4 w-4" />
                    Evaluate Profile
                </button>
                {scores.last_evaluated && (
                    <div className={`text-xs text-gray-500 ${mono.className}`}>
                        Last evaluated: {format(new Date(scores.last_evaluated), 'MM/dd/yyyy, h:mm a')}
                    </div>
                )}
            </div>
        </div>
    );
} 