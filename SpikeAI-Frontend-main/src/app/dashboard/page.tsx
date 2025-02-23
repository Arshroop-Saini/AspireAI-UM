'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import ProfileEvaluationMeters from '@/components/ProfileEvaluationMeters';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Link from 'next/link';
import { format } from 'date-fns';

const inter = Inter({ subsets: ['latin'] });
const mono = JetBrains_Mono({ 
    subsets: ['latin'],
    variable: '--font-mono'
});

interface StudentContext {
    country: string;
    estimated_contribution: number;
    financial_aid_required: boolean;
    first_generation: boolean;
    ethnicity: string;
    gender: string;
    international_student: boolean;
}

interface StudentStatistics {
    class_rank: number;
    unweight_gpa: number;
    weight_gpa: number;
    sat_score: number;
}

interface StudentPreferences {
    campus_sizes: string[];
    college_types: string[];
    preferred_regions: string[];
    preferred_states: string[];
}

interface ExtracurricularActivity {
    name: string;
    activity_type: string;
    position_leadership: string;
    organization_description: string;
    activity_description: string;
    added_at?: string;
}

interface Award {
    title: string;
    grade_levels: string[];
    recognition_levels: string[];
    added_at?: string;
}

interface TargetCollege {
    name: string;
    type: string;
    added_at: string;
}

interface TargetActivity {
    name: string;
    description: string;
    hours_per_week: number;
    position: string;
    added_at: string;
    activity_type?: string;
}

interface StudentSubscription {
    is_subscribed: boolean;
    status: string;
    stripe_customer_id: string | null;
    stripe_subscription_id: string | null;
    plan_type: string | null;
    current_period_start: string | null;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
    payment_status: string | null;
    last_payment_date: string | null;
    features: string[];
}

interface StudentProfile {
    _id: string;
    auth0_id: string;
    email: string;
    name: string;
    picture: string;
    major: string;
    extracurriculars: ExtracurricularActivity[];
    awards: Award[];
    personality_type: string;
    student_context: StudentContext;
    student_statistics: StudentStatistics;
    student_preferences: StudentPreferences;
    student_theme: string;
    hooks: string[];
    target_colleges: TargetCollege[];
    target_activities: TargetActivity[];
    subscription: StudentSubscription;
    last_login: string;
    updated_at: string;
    evaluation_scores?: {
        testing_score: number;
        hsr_score: number;
        ecs_score: number;
        spiv_score: number;
        eval_score: number;
        last_evaluated: string;
    };
}

export default function Dashboard() {
    const [profile, setProfile] = useState<StudentProfile | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isEvaluating, setIsEvaluating] = useState(false);
    const { data: session } = useSession();
    const router = useRouter();

    const handleEvaluateProfile = async () => {
        try {
            setIsEvaluating(true);
            const response = await fetch('/api/profile-evaluation', {
                method: 'POST'
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to evaluate profile');
            }

            // Refetch profile to get updated evaluation scores
            const profileResponse = await fetch('/api/profile');
            const profileData = await profileResponse.json();

            if (!profileResponse.ok) {
                throw new Error(profileData.error || 'Failed to fetch updated profile');
            }

            setProfile(profileData.profile);
        } catch (err) {
            console.error('Profile evaluation error:', err);
        } finally {
            setIsEvaluating(false);
        }
    };

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                setIsLoading(true);
                const response = await fetch('/api/profile');
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to fetch profile');
                }

                // Initialize empty arrays and default values for missing fields
                const profileData = {
                    ...data.profile,
                    target_colleges: data.profile.target_colleges || [],
                    target_activities: data.profile.target_activities || [],
                    extracurriculars: data.profile.extracurriculars || [],
                    awards: data.profile.awards || [],
                    hooks: data.profile.hooks || [],
                    major: data.profile.major || '',
                    personality_type: data.profile.personality_type || '',
                    student_context: {
                        country: data.profile.student_context?.country || '',
                        estimated_contribution: data.profile.student_context?.estimated_contribution || 0,
                        financial_aid_required: data.profile.student_context?.financial_aid_required || false,
                        first_generation: data.profile.student_context?.first_generation || false,
                        ethnicity: data.profile.student_context?.ethnicity || '',
                        gender: data.profile.student_context?.gender || '',
                        international_student: data.profile.student_context?.international_student || false
                    },
                    student_statistics: {
                        class_rank: data.profile.student_statistics?.class_rank || 0,
                        unweight_gpa: data.profile.student_statistics?.unweight_gpa || 0,
                        weight_gpa: data.profile.student_statistics?.weight_gpa || 0,
                        sat_score: data.profile.student_statistics?.sat_score || 0
                    },
                    student_preferences: {
                        campus_sizes: data.profile.student_preferences?.campus_sizes || [],
                        college_types: data.profile.student_preferences?.college_types || [],
                        preferred_regions: data.profile.student_preferences?.preferred_regions || [],
                        preferred_states: data.profile.student_preferences?.preferred_states || []
                    }
                };

                setProfile(profileData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
                console.error('Profile fetch error:', err);
            } finally {
                setIsLoading(false);
            }
        };

        if (session?.user) {
            fetchProfile();
        }
    }, [session, router]);

    if (!session) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black">
                <div className="text-center">
                    <h1 className={`text-2xl font-bold text-white mb-4 ${mono.className}`}>Welcome to AspireAI</h1>
                    <p className={`text-gray-400 mb-6 ${mono.className}`}>Please sign in to access your dashboard</p>
                    <button
                        onClick={() => router.push('/auth/signin')}
                        className={`bg-[#E87C3E] text-white px-6 py-2 rounded-lg hover:bg-[#FF8D4E] transition-colors ${mono.className}`}
                    >
                        Sign In
                    </button>
                </div>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black">
                <div className={`text-white ${mono.className}`}>Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-black min-h-screen">
                <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            </div>
        );
    }

    // Check if essential profile sections are complete
    const isProfileComplete = profile && (
        profile.major &&
        profile.personality_type &&
        profile.student_context &&
        profile.student_statistics &&
        profile.student_preferences &&
        profile.extracurriculars.length > 0
    );

    if (!isProfileComplete) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black">
                <div className="text-center">
                    <h1 className={`text-2xl font-bold text-white mb-4 ${mono.className}`}>Welcome to SpikeAI</h1>
                    <p className={`text-gray-400 mb-6 ${mono.className}`}>Please complete your profile to see your full dashboard</p>
                    <button
                        onClick={() => router.push('/profile')}
                        className={`bg-[#E87C3E] text-white px-6 py-2 rounded-lg hover:bg-[#FF8D4E] transition-colors ${mono.className}`}
                    >
                        Complete Profile
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={`min-h-screen bg-black text-white ${inter.className} ${mono.className}`}>
            {/* Profile Evaluation Section */}
            <section className="p-6 bg-[#111111] rounded-lg mb-6 mx-auto max-w-[90%] mt-8">
                <div className="mb-8">
                    <h2 className={`text-xl flex items-center gap-2 ${mono.className}`}>
                        <span className="text-[#E87C3E]">|</span>
                        Profile Evaluation
                    </h2>
                </div>
                {profile?.evaluation_scores ? (
                    <ProfileEvaluationMeters
                        scores={profile.evaluation_scores}
                        mono={mono}
                    />
                ) : (
                    <div className="text-center py-8">
                        <p className="text-gray-400 mb-4">Your profile needs to be evaluated</p>
                        <button
                            onClick={handleEvaluateProfile}
                            disabled={isEvaluating}
                            className={`bg-[#E87C3E] text-white px-6 py-2 rounded-lg hover:bg-[#FF8D4E] transition-colors ${mono.className} disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            {isEvaluating ? 'Evaluating...' : 'Evaluate Profile'}
                        </button>
                    </div>
                )}
            </section>

            {/* Student Theme Section */}
            <section className="p-6 bg-[#111111] rounded-lg mb-6 mx-auto max-w-[90%]">
                <div className="mb-8">
                    <h2 className={`text-xl flex items-center gap-2 ${mono.className}`}>
                        <span className="text-[#E87C3E]">|</span>
                        { profile.name} Spike
                    </h2>
                </div>
                <div className="p-6 rounded-lg bg-[#1A1A1A] border border-gray-800">
                    <p className={`text-gray-400 ${mono.className}`}>{profile.student_theme || 'Theme not set'}</p>
                </div>
            </section>

            {/* Targets to Achieve Section */}
            <section className="p-6 bg-[#111111] rounded-lg mb-6 mx-auto max-w-[90%]">
                <h2 className={`text-xl flex items-center gap-2 mb-8 ${mono.className}`}>
                    <span className="text-[#E87C3E]">|</span>
                    Targets to Achieve
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Target Colleges */}
                    <div className="p-6 rounded-lg bg-[#1A1A1A] border border-gray-800">
                        <h3 className={`text-lg mb-6 ${mono.className} flex items-center gap-2`}>
                            Target Colleges
                        </h3>
                        {profile.target_colleges && profile.target_colleges.length > 0 ? (
                            <div className="grid grid-cols-1 gap-4">
                                {profile.target_colleges.map((college, index) => (
                                    <div key={index} className="p-4 rounded-lg bg-[#2A2A2A] border border-gray-800 hover:border-gray-700 transition-all duration-300">
                                        <h4 className={`text-base mb-2 ${mono.className}`}>{college.name}</h4>
                                        <span className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                            {college.type}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-4 rounded-lg bg-[#2A2A2A] border border-gray-800">
                                <p className={`text-gray-400 text-sm ${mono.className}`}>No target colleges added yet.</p>
                                <Link href="/college-list" className="text-[#E87C3E] text-sm hover:text-[#FF8D4E] mt-2 inline-block transition-colors">
                                    Update Profile
                                </Link>
                            </div>
                        )}
                    </div>

                    {/* Target Activities */}
                    <div className="p-6 rounded-lg bg-[#1A1A1A] border border-gray-800">
                        <h3 className={`text-lg mb-6 ${mono.className} flex items-center gap-2`}>
                            Target Activities
                        </h3>
                        {profile.target_activities && profile.target_activities.length > 0 ? (
                            <div className="grid grid-cols-1 gap-4">
                                {profile.target_activities.map((activity, index) => (
                                    <div key={index} className="p-4 rounded-lg bg-[#2A2A2A] border border-gray-800 hover:border-gray-700 transition-all duration-300">
                                        <h4 className={`text-base mb-2 ${mono.className}`}>{activity.name}</h4>
                                        <div className="flex flex-wrap gap-2 mb-2">
                                            <span className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                {activity.activity_type || 'Other'}
                                            </span>
                                            <span className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                {activity.hours_per_week} hrs/week
                                            </span>
                                            {activity.position && (
                                                <span className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                    {activity.position}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-gray-400 mt-2">{activity.description}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-4 rounded-lg bg-[#2A2A2A] border border-gray-800">
                                <p className={`text-gray-400 text-sm ${mono.className}`}>No target activities added yet.</p>
                                <Link href="/ec-suggestions" className="text-[#E87C3E] text-sm hover:text-[#FF8D4E] mt-2 inline-block transition-colors">
                                    Update Profile
                                </Link>
                            </div>
                        )}
                    </div>
                </div>
            </section>

            {/* Profile Details Section */}
            <section className="p-6 bg-[#111111] rounded-lg mb-6 mx-auto max-w-[90%]">
                <h2 className={`text-xl flex items-center gap-2 mb-8 ${mono.className}`}>
                    <span className="text-[#E87C3E]">|</span>
                    Profile Details
                </h2>
                
                {/* Basic Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                    <div className="p-6 rounded-lg bg-[#1A1A1A] border border-gray-800">
                        <h3 className={`text-lg mb-6 ${mono.className}`}>Basic Information</h3>
                        <div className="grid grid-cols-1 gap-6">
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">👤</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>Name</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.name || 'Not set'}</div>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">📧</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>Email</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.email || 'Not set'}</div>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">🎓</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>Major</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.major || 'Not set'}</div>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">🧠</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>Personality Type</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.personality_type || 'Not set'}</div>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">🎯</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>Hooks</div>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                        {profile.hooks && profile.hooks.length > 0 ? (
                                            profile.hooks.map((hook, index) => (
                                                <span key={index} className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                    {hook}
                                                </span>
                                            ))
                                        ) : (
                                            <span className={`text-gray-400 ${mono.className}`}>No hooks set</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Statistics */}
                    <div className="p-6 rounded-lg bg-[#1A1A1A] border border-gray-800">
                        <h3 className={`text-lg mb-6 ${mono.className}`}>Statistics</h3>
                        <div className="grid grid-cols-1 gap-6">
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">🏆</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>Class Rank</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.student_statistics.class_rank || 'Not set'}</div>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">📊</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>Unweighted GPA</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.student_statistics.unweight_gpa || 'Not set'}</div>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">📊</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>Weighted GPA</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.student_statistics.weight_gpa || 'Not set'}</div>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">📝</div>
                        <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>SAT Score</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.student_statistics.sat_score || 'Not set'}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Student Context and College Preferences */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                    {/* Student Context */}
                    <div className="p-6 rounded-lg bg-[#1A1A1A] border border-gray-800">
                        <h3 className={`text-lg mb-6 ${mono.className}`}>Student Context</h3>
                        <div className="grid grid-cols-1 gap-4">
                            {profile.student_context.country && (
                                <div className="flex items-start gap-4">
                                    <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">🌍</div>
                                    <div>
                                        <div className={`text-sm text-gray-400 ${mono.className}`}>Country</div>
                                        <div className={`mt-1 ${mono.className}`}>{profile.student_context.country}</div>
                                    </div>
                                </div>
                            )}
                            {profile.student_context.ethnicity && (
                                <div className="flex items-start gap-4">
                                    <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">👥</div>
                                    <div>
                                        <div className={`text-sm text-gray-400 ${mono.className}`}>Ethnicity</div>
                                        <div className={`mt-1 ${mono.className}`}>{profile.student_context.ethnicity}</div>
                                    </div>
                                </div>
                            )}
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">🎓</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>First Generation</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.student_context.first_generation ? 'Yes' : 'No'}</div>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">✈️</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>International Student</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.student_context.international_student ? 'Yes' : 'No'}</div>
                                </div>
                            </div>
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#2A2A2A] text-[#E87C3E]">💰</div>
                                <div>
                                    <div className={`text-sm text-gray-400 ${mono.className}`}>Financial Aid Required</div>
                                    <div className={`mt-1 ${mono.className}`}>{profile.student_context.financial_aid_required ? 'Yes' : 'No'}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* College Preferences */}
                    <div className="p-6 rounded-lg bg-[#1A1A1A] border border-gray-800">
                        <h3 className={`text-lg mb-6 ${mono.className}`}>College Preferences</h3>
                        <div className="space-y-6">
                            {profile.student_preferences.campus_sizes.length > 0 && (
                                <div>
                                    <div className={`text-sm text-gray-400 mb-2 ${mono.className}`}>Campus Sizes</div>
                                    <div className="flex flex-wrap gap-2">
                                        {profile.student_preferences.campus_sizes.map((size, index) => (
                                            <span key={index} className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                {size}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {profile.student_preferences.college_types.length > 0 && (
                                <div>
                                    <div className={`text-sm text-gray-400 mb-2 ${mono.className}`}>College Types</div>
                                    <div className="flex flex-wrap gap-2">
                                        {profile.student_preferences.college_types.map((type, index) => (
                                            <span key={index} className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                {type}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {profile.student_preferences.preferred_regions.length > 0 && (
                                <div>
                                    <div className={`text-sm text-gray-400 mb-2 ${mono.className}`}>Preferred Regions</div>
                                    <div className="flex flex-wrap gap-2">
                                        {profile.student_preferences.preferred_regions.map((region, index) => (
                                            <span key={index} className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                {region}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {profile.student_preferences.preferred_states.length > 0 && (
                                <div>
                                    <div className={`text-sm text-gray-400 mb-2 ${mono.className}`}>Preferred States</div>
                                    <div className="flex flex-wrap gap-2">
                                        {profile.student_preferences.preferred_states.map((state, index) => (
                                            <span key={index} className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                {state}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                        </div>
                    </div>

                {/* Extracurriculars and Awards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Extracurricular Activities */}
                    <div className="p-6 rounded-lg bg-[#1A1A1A] border border-gray-800">
                        <h3 className={`text-lg mb-6 ${mono.className} flex items-center gap-2`}>
                            <span className="text-[#E87C3E]">|</span>
                            Extracurricular Activities
                        </h3>
                        <div className="grid grid-cols-1 gap-4">
                            {profile.extracurriculars.length > 0 ? (
                                profile.extracurriculars.map((activity, index) => (
                                    <div key={index} className="p-4 rounded-lg bg-[#2A2A2A] border border-gray-800 hover:border-gray-700 transition-all duration-300">
                                        <h4 className={`text-base mb-2 ${mono.className}`}>{activity.name}</h4>
                                        <div className="flex flex-wrap gap-2 mb-2">
                                            <span className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                {activity.activity_type || 'Other'}
                                            </span>
                                            <span className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                {activity.position_leadership}
                                            </span>
                                        </div>
                                        <div className="space-y-2">
                                            <p className={`text-sm text-gray-400 ${mono.className}`}>
                                                <span className="font-semibold">Organization:</span> {activity.organization_description}
                                            </p>
                                            <p className={`text-sm text-gray-400 ${mono.className}`}>
                                                <span className="font-semibold">Description:</span> {activity.activity_description}
                                            </p>
                                            {activity.added_at && (
                                                <p className={`text-xs text-gray-500 mt-2 ${mono.className}`}>
                                                    Added {format(new Date(activity.added_at), 'MMM d, yyyy')}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="p-4 rounded-lg bg-[#2A2A2A] border border-gray-800">
                                    <p className={`text-gray-400 text-sm ${mono.className}`}>No extracurricular activities added yet.</p>
                                    <Link href="/profile" className="text-[#E87C3E] text-sm hover:text-[#FF8D4E] mt-2 inline-block transition-colors">
                                        Update Profile
                                    </Link>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Awards */}
                    <div className="p-6 rounded-lg bg-[#1A1A1A] border border-gray-800">
                        <h3 className={`text-lg mb-6 ${mono.className} flex items-center gap-2`}>
                            <span className="text-[#E87C3E]">|</span>
                            Awards & Achievements
                        </h3>
                        <div className="grid grid-cols-1 gap-4">
                            {profile.awards.length > 0 ? (
                                profile.awards.map((award, index) => (
                                    <div key={index} className="p-4 rounded-lg bg-[#2A2A2A] border border-gray-800 hover:border-gray-700 transition-all duration-300">
                                        <h4 className={`text-base mb-2 ${mono.className}`}>{award.title}</h4>
                                        <div className="flex flex-wrap gap-2 mb-2">
                                            {award.grade_levels.map((grade, gradeIndex) => (
                                                <span key={gradeIndex} className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                    Grade {grade}
                                                </span>
                                            ))}
                                            {award.recognition_levels.map((level, levelIndex) => (
                                                <span key={levelIndex} className={`px-3 py-1 bg-[#2A2A2A] rounded-full text-sm text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors ${mono.className}`}>
                                                    {level}
                                                </span>
                                            ))}
                                        </div>
                                        {award.added_at && (
                                            <p className={`text-xs text-gray-500 mt-2 ${mono.className}`}>
                                                Added {format(new Date(award.added_at), 'MMM d, yyyy')}
                                            </p>
                                        )}
                                    </div>
                                ))
                            ) : (
                                <div className="p-4 rounded-lg bg-[#2A2A2A] border border-gray-800">
                                    <p className={`text-gray-400 text-sm ${mono.className}`}>No awards added yet.</p>
                                    <Link href="/profile" className="text-[#E87C3E] text-sm hover:text-[#FF8D4E] mt-2 inline-block transition-colors">
                                        Update Profile
                                    </Link>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
} 
