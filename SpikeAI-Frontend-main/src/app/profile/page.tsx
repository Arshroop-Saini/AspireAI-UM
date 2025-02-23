'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { mono } from '@/lib/fonts';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

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

interface Profile {
    _id?: string;
    email: string;
    name: string;
    major: string;
    personality_type: string;
    student_statistics: {
        class_rank: number;
        unweight_gpa: number;
        weight_gpa: number;
        sat_score: number;
    };
    student_context: {
        country: string;
        estimated_contribution: number;
        financial_aid_required: boolean;
        first_generation: boolean;
        ethnicity: string;
        gender: string;
        international_student: boolean;
    };
    student_preferences: {
        campus_sizes: string[];
        college_types: string[];
        preferred_regions: string[];
        preferred_states: string[];
    };
    extracurriculars: ExtracurricularActivity[];
    awards: Award[];
    hooks: string[];
    target_colleges: Array<{
        name: string;
        type: string;
        added_at: string;
    }>;
    student_theme: string;
}

const INITIAL_PROFILE: Profile = {
    email: '',
    name: '',
    major: '',
    personality_type: '',
    student_statistics: {
        class_rank: 0,
        unweight_gpa: 0,
        weight_gpa: 0,
        sat_score: 0
    },
    student_context: {
        country: '',
        estimated_contribution: 0,
        financial_aid_required: false,
        first_generation: false,
        ethnicity: '',
        gender: '',
        international_student: false
    },
    student_preferences: {
        campus_sizes: [],
        college_types: [],
        preferred_regions: [],
        preferred_states: []
    },
    extracurriculars: [],
    awards: [],
    hooks: [],
    target_colleges: [],
    student_theme: ''
};

const PERSONALITY_TYPES = [
    'INTJ', 'INTP', 'ENTJ', 'ENTP',  // Analysts
    'INFJ', 'INFP', 'ENFJ', 'ENFP',  // Diplomats
    'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',  // Sentinels
    'ISTP', 'ISFP', 'ESTP', 'ESFP'   // Explorers
];

const HOOKS = [
    'First-Generation College Student',
    'International Student',
    'Legacy Student',
    'Student Athlete',
    'Military Background',
    'Rural Background',
    'Inner City Background',
    'Immigrant Background',
    'Disadvantaged Background',
    'Overcoming Adversity',
    'Unique Cultural Perspective',
    'Exceptional Talent',
    'Research Experience',
    'Entrepreneurial Spirit',
    'Community Impact',
    'Leadership Experience',
    'Social Justice Advocate',
    'Environmental Activist',
    'Innovation/Invention',
    'Artistic Achievement'
];

const US_STATES = [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
    'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
    'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa',
    'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
    'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri',
    'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey',
    'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
    'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
    'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
    'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
];

export default function ProfilePage() {
    const { data: session, status } = useSession();
    const router = useRouter();
    const [profile, setProfile] = useState<Profile>(INITIAL_PROFILE);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    const [originalProfile, setOriginalProfile] = useState<Profile>(INITIAL_PROFILE);
    const [newCollegeName, setNewCollegeName] = useState('');
    const [newCollegeType, setNewCollegeType] = useState('');

    const fetchProfile = useCallback(async () => {
        if (!session?.id_token) {
            setLoading(false);
            return;
        }

        try {
            const response = await fetch('/api/profile/', {
                headers: {
                    'Authorization': `Bearer ${session.id_token}`,
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch profile');
            }
            
            const data = await response.json();
            console.log('Profile response:', data); // Debug log
            
            if (!data.success || !data.profile) {
                throw new Error('Invalid profile data received');
            }
            
            setProfile(data.profile);
            setOriginalProfile(data.profile);
            setError(null);
        } catch (err) {
            console.error('Profile fetch error:', err);
            setError(err instanceof Error ? err.message : 'Failed to load profile');
        } finally {
            setLoading(false);
        }
    }, [session?.id_token]);

    useEffect(() => {
        if (status === 'unauthenticated') {
            router.push('/login');
            return;
        }
        
        if (status === 'authenticated') {
            fetchProfile();
        }
    }, [status, router, fetchProfile]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            if (!session?.id_token) {
                throw new Error('Not authenticated');
            }

            // Create a copy of the profile with initialized arrays
            const updatedProfile: Profile = {
                ...profile,
                target_colleges: profile.target_colleges || [],
                extracurriculars: profile.extracurriculars || [],
                awards: profile.awards || [],
                hooks: profile.hooks || [],
                student_preferences: {
                    ...profile.student_preferences,
                    campus_sizes: profile.student_preferences?.campus_sizes || [],
                    college_types: profile.student_preferences?.college_types || [],
                    preferred_regions: profile.student_preferences?.preferred_regions || [],
                    preferred_states: profile.student_preferences?.preferred_states || []
                }
            };

            // Get only the changed fields
            type ProfileKey = keyof Profile;
            const changedFields = Object.keys(updatedProfile).reduce((acc: Record<string, unknown>, key) => {
                // Skip _id field
                if (key === '_id') return acc;

                const currentValue = updatedProfile[key as ProfileKey];
                const originalValue = originalProfile[key as ProfileKey];

                // Special handling for arrays and objects
                if (Array.isArray(currentValue)) {
                    // For target_colleges and other arrays, always include if they're different
                    // This ensures empty arrays are properly saved
                    if (JSON.stringify(currentValue) !== JSON.stringify(originalValue)) {
                        acc[key] = currentValue;
                    }
                } else if (typeof currentValue === 'object' && currentValue !== null) {
                    // For nested objects, compare stringified versions
                    if (JSON.stringify(currentValue) !== JSON.stringify(originalValue)) {
                        acc[key] = currentValue;
                    }
                } else if (currentValue !== originalValue) {
                    // For primitive values
                    acc[key] = currentValue;
                }

                return acc;
            }, {});

            // If no fields have changed, don't make the API call
            if (Object.keys(changedFields).length === 0) {
                setMessage('No changes to update');
                setLoading(false);
                return;
            }

            console.log('Sending profile update with changed fields:', changedFields);

            const response = await fetch('/api/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${session.id_token}`
                },
                body: JSON.stringify(changedFields)
            });

            const data = await response.json();
            console.log('Profile update response:', data);

            if (!response.ok) {
                throw new Error(data.error || `Failed to update profile: ${response.status}`);
            }

            if (!data.success) {
                throw new Error(data.error || 'Failed to update profile: Unknown error');
            }

            // Update the original profile with the new data
            setOriginalProfile(updatedProfile);
            // Refresh the profile data after successful update
            await fetchProfile();
            setMessage('Profile updated successfully');
            setTimeout(() => setMessage(null), 3000);

        } catch (error) {
            console.error('Profile update error:', error);
            setError(error instanceof Error ? error.message : 'Failed to update profile');
        } finally {
            setLoading(false);
        }
    };

    const handleContextChange = (
        field: keyof typeof profile.student_context,
        value: string | number | boolean
    ) => {
        setProfile({
            ...profile,
            student_context: {
                ...profile.student_context,
                [field]: value
            }
        });
    };

    const handleAddExtracurricular = () => {
        if (profile.extracurriculars.length >= 10) {
            setError("You can only add up to 10 extracurricular activities");
            return;
        }
        
        setProfile(prev => ({
            ...prev,
            extracurriculars: [
                ...prev.extracurriculars,
                {
                    name: '',
                    activity_type: '',
                    position_leadership: '',
                    organization_description: '',
                    activity_description: '',
                    added_at: new Date().toISOString()
                }
            ]
        }));
    };

    const handleExtracurricularChange = (index: number, field: keyof ExtracurricularActivity, value: string) => {
        setProfile(prev => ({
            ...prev,
            extracurriculars: prev.extracurriculars.map((activity, i) => 
                i === index ? { ...activity, [field]: value } : activity
            )
        }));
    };

    const handleRemoveExtracurricular = (index: number) => {
        setProfile(prev => ({
            ...prev,
            extracurriculars: prev.extracurriculars.filter((_, i) => i !== index)
        }));
    };

    const handleAddAward = () => {
        if (profile.awards.length >= 10) {
            setError("You can only add up to 10 awards");
            return;
        }
        
        setProfile(prev => ({
            ...prev,
            awards: [
                ...prev.awards,
                {
                    title: '',
                    grade_levels: [],
                    recognition_levels: [],
                    added_at: new Date().toISOString()
                }
            ]
        }));
    };

    const handleAwardChange = (index: number, field: keyof Award, value: string | string[]) => {
        setProfile(prev => ({
            ...prev,
            awards: prev.awards.map((award, i) => 
                i === index ? { ...award, [field]: value } : award
            )
        }));
    };

    const handleRemoveAward = (index: number) => {
        setProfile(prev => ({
            ...prev,
            awards: prev.awards.filter((_, i) => i !== index)
        }));
    };

    const handleAddCollege = () => {
        if (profile.target_colleges.length >= 10) {
            setError("You can only add up to 10 colleges");
            return;
        }
        
        setProfile(prev => ({
            ...prev,
            target_colleges: [
                ...prev.target_colleges,
                {
                    name: newCollegeName,
                    type: newCollegeType,
                    added_at: new Date().toISOString()
                }
            ]
        }));
        setNewCollegeName('');
        setNewCollegeType('');
    };

    const handleRemoveCollege = (index: number) => {
        // If this is the last college, we need to be extra careful with the update
        const isLastCollege = profile.target_colleges.length === 1;
        
        setProfile(prev => {
            const updatedColleges = prev.target_colleges.filter((_, i) => i !== index);
            const updatedProfile = {
                ...prev,
                target_colleges: updatedColleges
            };
            
            // If this was the last college, schedule the save after state update
            if (isLastCollege) {
                // Use setTimeout to ensure state update is complete
                setTimeout(() => {
                    const event = { preventDefault: () => {} } as React.FormEvent;
                    handleSubmit(event);
                }, 0);
            }
            
            return updatedProfile;
        });
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#0A0A0B]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E87C3E]"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black">
            <div className="container mx-auto px-4 py-8">
                <h1 className={`text-2xl font-bold mb-8 text-white ${mono.className}`}>Profile Settings</h1>
                
                {error && (
                    <Alert className="mb-4 border-red-500/20 bg-red-500/10">
                        <AlertDescription className="text-red-400">{error}</AlertDescription>
                    </Alert>
                )}
                
                {message && (
                    <Alert className="mb-4 border-green-500/20 bg-green-500/10">
                        <AlertDescription className="text-green-400">{message}</AlertDescription>
                    </Alert>
                )}

                <form onSubmit={handleSubmit} className="space-y-8">
                    {/* Basic Information Card */}
                    <Card className="border-zinc-800/40 bg-[#0A0A0B]">
                        <CardHeader>
                            <CardTitle className={`text-white ${mono.className}`}>
                                <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                                Basic Information
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <Label className={`text-zinc-300 ${mono.className}`}>Major</Label>
                                <Input
                                    type="text"
                                    value={profile?.major || ''}
                                    onChange={(e) => setProfile({ ...profile, major: e.target.value })}
                                    className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                />
                            </div>
                            <div>
                                <Label className={`text-zinc-300 ${mono.className}`}>Personality Type</Label>
                                <select
                                    value={profile?.personality_type || ''}
                                    onChange={(e) => setProfile({ ...profile, personality_type: e.target.value })}
                                    className={`w-full h-10 rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                >
                                    <option value="">Select Personality Type</option>
                                    {PERSONALITY_TYPES.map((type) => (
                                        <option key={type} value={type}>
                                            {type}
                                        </option>
                                    ))}
                                </select>
                                <p className={`text-sm text-zinc-400 mt-2 ${mono.className}`}>
                                    Not sure? Take a free test <a href="https://www.16personalities.com/free-personality-test" target="_blank" rel="noopener noreferrer" className="text-[#E87C3E] hover:underline">here</a>
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Academic Information and Personal Context Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Academic Information */}
                        <Card className="border-zinc-800/40 bg-[#0A0A0B]">
                            <CardHeader>
                                <CardTitle className={`text-white ${mono.className}`}>
                                    <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                                    Academic Information
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                            <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>Class Rank</Label>
                                    <Input
                                    type="number"
                                        value={profile?.student_statistics?.class_rank || ''}
                                    onChange={(e) => setProfile({
                                        ...profile,
                                        student_statistics: {
                                            ...profile.student_statistics,
                                            class_rank: parseInt(e.target.value) || 0
                                        }
                                    })}
                                        className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                />
                            </div>
                            <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>Unweighted GPA</Label>
                                    <Input
                                    type="number"
                                    step="0.01"
                                        value={profile?.student_statistics?.unweight_gpa || ''}
                                    onChange={(e) => setProfile({
                                        ...profile,
                                        student_statistics: {
                                            ...profile.student_statistics,
                                            unweight_gpa: parseFloat(e.target.value) || 0
                                        }
                                    })}
                                        className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                />
                            </div>
                            <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>Weighted GPA</Label>
                                    <Input
                                    type="number"
                                    step="0.01"
                                        value={profile?.student_statistics?.weight_gpa || ''}
                                    onChange={(e) => setProfile({
                                        ...profile,
                                        student_statistics: {
                                            ...profile.student_statistics,
                                            weight_gpa: parseFloat(e.target.value) || 0
                                        }
                                    })}
                                        className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                />
                            </div>
                            <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>SAT Score</Label>
                                    <Input
                                    type="number"
                                        value={profile?.student_statistics?.sat_score || ''}
                                    onChange={(e) => setProfile({
                                        ...profile,
                                        student_statistics: {
                                            ...profile.student_statistics,
                                            sat_score: parseInt(e.target.value) || 0
                                        }
                                    })}
                                        className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                />
                            </div>
                            </CardContent>
                        </Card>

                        {/* Personal Context */}
                        <Card className="border-zinc-800/40 bg-[#0A0A0B]">
                            <CardHeader>
                                <CardTitle className={`text-white ${mono.className}`}>
                                    <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                                    Personal Context
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                            <div>
                                    <Label htmlFor="country" className={`text-zinc-300 ${mono.className}`}>Country</Label>
                                    <select
                                        id="country"
                                        value={profile?.student_context?.country || ''}
                                    onChange={(e) => handleContextChange('country', e.target.value)}
                                        className={`w-full h-10 rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                    >
                                        <option value="">Select Country</option>
                                        <option value="Afghanistan">Afghanistan</option>
                                        <option value="Albania">Albania</option>
                                        <option value="Algeria">Algeria</option>
                                        <option value="Andorra">Andorra</option>
                                        <option value="Angola">Angola</option>
                                        <option value="Antigua and Barbuda">Antigua and Barbuda</option>
                                        <option value="Argentina">Argentina</option>
                                        <option value="Armenia">Armenia</option>
                                        <option value="Australia">Australia</option>
                                        <option value="Austria">Austria</option>
                                        <option value="Azerbaijan">Azerbaijan</option>
                                        <option value="Bahamas">Bahamas</option>
                                        <option value="Bahrain">Bahrain</option>
                                        <option value="Bangladesh">Bangladesh</option>
                                        <option value="Barbados">Barbados</option>
                                        <option value="Belarus">Belarus</option>
                                        <option value="Belgium">Belgium</option>
                                        <option value="Belize">Belize</option>
                                        <option value="Benin">Benin</option>
                                        <option value="Bhutan">Bhutan</option>
                                        <option value="Bolivia">Bolivia</option>
                                        <option value="Bosnia and Herzegovina">Bosnia and Herzegovina</option>
                                        <option value="Botswana">Botswana</option>
                                        <option value="Brazil">Brazil</option>
                                        <option value="Brunei">Brunei</option>
                                        <option value="Bulgaria">Bulgaria</option>
                                        <option value="Burkina Faso">Burkina Faso</option>
                                        <option value="Burundi">Burundi</option>
                                        <option value="Cabo Verde">Cabo Verde</option>
                                        <option value="Cambodia">Cambodia</option>
                                        <option value="Cameroon">Cameroon</option>
                                        <option value="Canada">Canada</option>
                                        <option value="Central African Republic">Central African Republic</option>
                                        <option value="Chad">Chad</option>
                                        <option value="Chile">Chile</option>
                                        <option value="China">China</option>
                                        <option value="Colombia">Colombia</option>
                                        <option value="Comoros">Comoros</option>
                                        <option value="Congo">Congo</option>
                                        <option value="Costa Rica">Costa Rica</option>
                                        <option value="Croatia">Croatia</option>
                                        <option value="Cuba">Cuba</option>
                                        <option value="Cyprus">Cyprus</option>
                                        <option value="Czech Republic">Czech Republic</option>
                                        <option value="Denmark">Denmark</option>
                                        <option value="Djibouti">Djibouti</option>
                                        <option value="Dominica">Dominica</option>
                                        <option value="Dominican Republic">Dominican Republic</option>
                                        <option value="Ecuador">Ecuador</option>
                                        <option value="Egypt">Egypt</option>
                                        <option value="El Salvador">El Salvador</option>
                                        <option value="Equatorial Guinea">Equatorial Guinea</option>
                                        <option value="Eritrea">Eritrea</option>
                                        <option value="Estonia">Estonia</option>
                                        <option value="Eswatini">Eswatini</option>
                                        <option value="Ethiopia">Ethiopia</option>
                                        <option value="Fiji">Fiji</option>
                                        <option value="Finland">Finland</option>
                                        <option value="France">France</option>
                                        <option value="Gabon">Gabon</option>
                                        <option value="Gambia">Gambia</option>
                                        <option value="Georgia">Georgia</option>
                                        <option value="Germany">Germany</option>
                                        <option value="Ghana">Ghana</option>
                                        <option value="Greece">Greece</option>
                                        <option value="Grenada">Grenada</option>
                                        <option value="Guatemala">Guatemala</option>
                                        <option value="Guinea">Guinea</option>
                                        <option value="Guinea-Bissau">Guinea-Bissau</option>
                                        <option value="Guyana">Guyana</option>
                                        <option value="Haiti">Haiti</option>
                                        <option value="Honduras">Honduras</option>
                                        <option value="Hungary">Hungary</option>
                                        <option value="Iceland">Iceland</option>
                                        <option value="India">India</option>
                                        <option value="Indonesia">Indonesia</option>
                                        <option value="Iran">Iran</option>
                                        <option value="Iraq">Iraq</option>
                                        <option value="Ireland">Ireland</option>
                                        <option value="Israel">Israel</option>
                                        <option value="Italy">Italy</option>
                                        <option value="Jamaica">Jamaica</option>
                                        <option value="Japan">Japan</option>
                                        <option value="Jordan">Jordan</option>
                                        <option value="Kazakhstan">Kazakhstan</option>
                                        <option value="Kenya">Kenya</option>
                                        <option value="Kiribati">Kiribati</option>
                                        <option value="Korea, North">Korea, North</option>
                                        <option value="Korea, South">Korea, South</option>
                                        <option value="Kosovo">Kosovo</option>
                                        <option value="Kuwait">Kuwait</option>
                                        <option value="Kyrgyzstan">Kyrgyzstan</option>
                                        <option value="Laos">Laos</option>
                                        <option value="Latvia">Latvia</option>
                                        <option value="Lebanon">Lebanon</option>
                                        <option value="Lesotho">Lesotho</option>
                                        <option value="Liberia">Liberia</option>
                                        <option value="Libya">Libya</option>
                                        <option value="Liechtenstein">Liechtenstein</option>
                                        <option value="Lithuania">Lithuania</option>
                                        <option value="Luxembourg">Luxembourg</option>
                                        <option value="Madagascar">Madagascar</option>
                                        <option value="Malawi">Malawi</option>
                                        <option value="Malaysia">Malaysia</option>
                                        <option value="Maldives">Maldives</option>
                                        <option value="Mali">Mali</option>
                                        <option value="Malta">Malta</option>
                                        <option value="Marshall Islands">Marshall Islands</option>
                                        <option value="Mauritania">Mauritania</option>
                                        <option value="Mauritius">Mauritius</option>
                                        <option value="Mexico">Mexico</option>
                                        <option value="Micronesia">Micronesia</option>
                                        <option value="Moldova">Moldova</option>
                                        <option value="Monaco">Monaco</option>
                                        <option value="Mongolia">Mongolia</option>
                                        <option value="Montenegro">Montenegro</option>
                                        <option value="Morocco">Morocco</option>
                                        <option value="Mozambique">Mozambique</option>
                                        <option value="Myanmar">Myanmar</option>
                                        <option value="Namibia">Namibia</option>
                                        <option value="Nauru">Nauru</option>
                                        <option value="Nepal">Nepal</option>
                                        <option value="Netherlands">Netherlands</option>
                                        <option value="New Zealand">New Zealand</option>
                                        <option value="Nicaragua">Nicaragua</option>
                                        <option value="Niger">Niger</option>
                                        <option value="Nigeria">Nigeria</option>
                                        <option value="North Macedonia">North Macedonia</option>
                                        <option value="Norway">Norway</option>
                                        <option value="Oman">Oman</option>
                                        <option value="Pakistan">Pakistan</option>
                                        <option value="Palau">Palau</option>
                                        <option value="Palestine">Palestine</option>
                                        <option value="Panama">Panama</option>
                                        <option value="Papua New Guinea">Papua New Guinea</option>
                                        <option value="Paraguay">Paraguay</option>
                                        <option value="Peru">Peru</option>
                                        <option value="Philippines">Philippines</option>
                                        <option value="Poland">Poland</option>
                                        <option value="Portugal">Portugal</option>
                                        <option value="Qatar">Qatar</option>
                                        <option value="Romania">Romania</option>
                                        <option value="Russia">Russia</option>
                                        <option value="Rwanda">Rwanda</option>
                                        <option value="Saint Kitts and Nevis">Saint Kitts and Nevis</option>
                                        <option value="Saint Lucia">Saint Lucia</option>
                                        <option value="Saint Vincent and the Grenadines">Saint Vincent and the Grenadines</option>
                                        <option value="Samoa">Samoa</option>
                                        <option value="San Marino">San Marino</option>
                                        <option value="Sao Tome and Principe">Sao Tome and Principe</option>
                                        <option value="Saudi Arabia">Saudi Arabia</option>
                                        <option value="Senegal">Senegal</option>
                                        <option value="Serbia">Serbia</option>
                                        <option value="Seychelles">Seychelles</option>
                                        <option value="Sierra Leone">Sierra Leone</option>
                                        <option value="Singapore">Singapore</option>
                                        <option value="Slovakia">Slovakia</option>
                                        <option value="Slovenia">Slovenia</option>
                                        <option value="Solomon Islands">Solomon Islands</option>
                                        <option value="Somalia">Somalia</option>
                                        <option value="South Africa">South Africa</option>
                                        <option value="South Sudan">South Sudan</option>
                                        <option value="Spain">Spain</option>
                                        <option value="Sri Lanka">Sri Lanka</option>
                                        <option value="Sudan">Sudan</option>
                                        <option value="Suriname">Suriname</option>
                                        <option value="Sweden">Sweden</option>
                                        <option value="Switzerland">Switzerland</option>
                                        <option value="Syria">Syria</option>
                                        <option value="Taiwan">Taiwan</option>
                                        <option value="Tajikistan">Tajikistan</option>
                                        <option value="Tanzania">Tanzania</option>
                                        <option value="Thailand">Thailand</option>
                                        <option value="Timor-Leste">Timor-Leste</option>
                                        <option value="Togo">Togo</option>
                                        <option value="Tonga">Tonga</option>
                                        <option value="Trinidad and Tobago">Trinidad and Tobago</option>
                                        <option value="Tunisia">Tunisia</option>
                                        <option value="Turkey">Turkey</option>
                                        <option value="Turkmenistan">Turkmenistan</option>
                                        <option value="Tuvalu">Tuvalu</option>
                                        <option value="Uganda">Uganda</option>
                                        <option value="Ukraine">Ukraine</option>
                                        <option value="United Arab Emirates">United Arab Emirates</option>
                                        <option value="United Kingdom">United Kingdom</option>
                                        <option value="United States">United States</option>
                                        <option value="Uruguay">Uruguay</option>
                                        <option value="Uzbekistan">Uzbekistan</option>
                                        <option value="Vanuatu">Vanuatu</option>
                                        <option value="Vatican City">Vatican City</option>
                                        <option value="Venezuela">Venezuela</option>
                                        <option value="Vietnam">Vietnam</option>
                                        <option value="Yemen">Yemen</option>
                                        <option value="Zambia">Zambia</option>
                                        <option value="Zimbabwe">Zimbabwe</option>
                                    </select>
                            </div>
                            <div>
                                    <Label htmlFor="gender" className={`text-zinc-300 ${mono.className}`}>Gender</Label>
                                    <select
                                        id="gender"
                                        value={profile.student_context.gender}
                                        onChange={(e) => handleContextChange('gender', e.target.value)}
                                        className={`w-full h-10 rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                    >
                                        <option value="">Select Gender</option>
                                        <option value="Male">Male</option>
                                        <option value="Female">Female</option>
                                        <option value="Non-binary">Non-binary</option>
                                        <option value="Other">Other</option>
                                        <option value="Prefer not to say">Prefer not to say</option>
                                    </select>
                            </div>
                            <div>
                                    <Label htmlFor="ethnicity" className={`text-zinc-300 ${mono.className}`}>Ethnicity</Label>
                                <select
                                        id="ethnicity"
                                        value={profile.student_context.ethnicity}
                                    onChange={(e) => handleContextChange('ethnicity', e.target.value)}
                                        className={`w-full h-10 rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                >
                                    <option value="">Select Ethnicity</option>
                                        <option value="American Indian or Alaska Native">American Indian or Alaska Native</option>
                                        <option value="Asian">Asian</option>
                                        <option value="Black or African American">Black or African American</option>
                                        <option value="Hispanic or Latino">Hispanic or Latino</option>
                                        <option value="Native Hawaiian or Other Pacific Islander">Native Hawaiian or Other Pacific Islander</option>
                                        <option value="White">White</option>
                                        <option value="Two or More Races">Two or More Races</option>
                                        <option value="Other">Other</option>
                                        <option value="Prefer not to say">Prefer not to say</option>
                                </select>
                            </div>
                            <div>
                                    <Label htmlFor="estimated_contribution" className={`text-zinc-300 ${mono.className}`}>Estimated Contribution</Label>
                                    <Input
                                        id="estimated_contribution"
                                        type="number"
                                        value={profile.student_context.estimated_contribution}
                                        onChange={(e) => handleContextChange('estimated_contribution', parseFloat(e.target.value))}
                                        className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                    />
                            </div>
                                <div className="grid grid-cols-1 gap-4">
                                    <div>
                                        <Label htmlFor="financial_aid_required" className={`text-zinc-300 ${mono.className}`}>Financial Aid Required</Label>
                                        <div className="flex items-center mt-2">
                                <input
                                                id="financial_aid_required"
                                    type="checkbox"
                                                checked={profile.student_context.financial_aid_required}
                                    onChange={(e) => handleContextChange('financial_aid_required', e.target.checked)}
                                                className="h-4 w-4 rounded border-zinc-800 bg-[#0A0A0B] text-[#E87C3E] focus:ring-[#E87C3E]"
                                />
                                            <span className="ml-2 text-sm text-zinc-400">Yes</span>
                            </div>
                                    </div>
                                    <div>
                                        <Label htmlFor="first_generation" className={`text-zinc-300 ${mono.className}`}>First Generation Student</Label>
                                        <div className="flex items-center mt-2">
                                <input
                                                id="first_generation"
                                    type="checkbox"
                                                checked={profile.student_context.first_generation}
                                    onChange={(e) => handleContextChange('first_generation', e.target.checked)}
                                                className="h-4 w-4 rounded border-zinc-800 bg-[#0A0A0B] text-[#E87C3E] focus:ring-[#E87C3E]"
                                />
                                            <span className="ml-2 text-sm text-zinc-400">Yes</span>
                            </div>
                                    </div>
                                    <div>
                                        <Label htmlFor="international_student" className={`text-zinc-300 ${mono.className}`}>International Student</Label>
                                        <div className="flex items-center mt-2">
                                <input
                                                id="international_student"
                                    type="checkbox"
                                                checked={profile.student_context.international_student}
                                    onChange={(e) => handleContextChange('international_student', e.target.checked)}
                                                className="h-4 w-4 rounded border-zinc-800 bg-[#0A0A0B] text-[#E87C3E] focus:ring-[#E87C3E]"
                                />
                                            <span className="ml-2 text-sm text-zinc-400">Yes</span>
                            </div>
                        </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Extracurricular Activities Section */}
                    <Card className="border-zinc-800/40 bg-[#0A0A0B]">
                        <CardHeader>
                            <CardTitle className={`text-white ${mono.className}`}>
                                <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                                Extracurricular Activities
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="flex justify-between items-center">
                                <Label className={`text-zinc-300 ${mono.className}`}>Activities</Label>
                                <Button
                                        type="button"
                                        onClick={handleAddExtracurricular}
                                        disabled={profile.extracurriculars.length >= 10}
                                    className={`px-4 py-2 bg-[#E87C3E] text-white rounded-md hover:bg-[#FF8D4E] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#E87C3E] ${mono.className}`}
                                    >
                                        Add Activity
                                </Button>
                                </div>
                            <div className="space-y-6">
                                    {profile.extracurriculars.map((activity, index) => (
                                    <div key={index} className="border border-zinc-800/40 rounded-lg p-6 space-y-4 relative bg-[#121214]">
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveExtracurricular(index)}
                                            className="absolute top-4 right-4 text-zinc-500 hover:text-red-500 transition-colors"
                                            >
                                                ×
                                            </button>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <Label className={`text-zinc-300 ${mono.className}`}>Activity Name</Label>
                                                <Input
                                                    type="text"
                                                    value={activity.name}
                                                    onChange={(e) => handleExtracurricularChange(index, 'name', e.target.value)}
                                                    className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                                />
                                            </div>
                                            <div>
                                                <Label className={`text-zinc-300 ${mono.className}`}>Activity Type</Label>
                                                <Input
                                                    type="text"
                                                    value={activity.activity_type}
                                                    onChange={(e) => handleExtracurricularChange(index, 'activity_type', e.target.value)}
                                                    className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                                />
                                            </div>
                                            <div>
                                                <Label className={`text-zinc-300 ${mono.className}`}>Position/Leadership</Label>
                                                <Input
                                                    type="text"
                                                    value={activity.position_leadership}
                                                    onChange={(e) => handleExtracurricularChange(index, 'position_leadership', e.target.value)}
                                                    className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                                />
                                            </div>
                                            <div>
                                                <Label className={`text-zinc-300 ${mono.className}`}>Organization</Label>
                                                <Input
                                                    type="text"
                                                    value={activity.organization_description}
                                                    onChange={(e) => handleExtracurricularChange(index, 'organization_description', e.target.value)}
                                                    className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                                />
                                            </div>
                                            <div className="md:col-span-2">
                                                <Label className={`text-zinc-300 ${mono.className}`}>Activity Description</Label>
                                <textarea
                                                    value={activity.activity_description}
                                                    onChange={(e) => handleExtracurricularChange(index, 'activity_description', e.target.value)}
                                                    rows={3}
                                                    className={`w-full rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                                />
                                            </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                        </CardContent>
                    </Card>

                    {/* Awards and Honors Section */}
                    <Card className="border-zinc-800/40 bg-[#0A0A0B]">
                        <CardHeader>
                            <CardTitle className={`text-white ${mono.className}`}>
                                <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                                Awards & Honors
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="flex justify-between items-center">
                                <Label className={`text-zinc-300 ${mono.className}`}>Awards & Honors</Label>
                                <Button
                                        type="button"
                                        onClick={handleAddAward}
                                        disabled={profile.awards.length >= 10}
                                    className={`px-4 py-2 bg-[#E87C3E] text-white rounded-md hover:bg-[#FF8D4E] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#E87C3E] ${mono.className}`}
                                    >
                                        Add Award
                                </Button>
                                </div>
                            <div className="space-y-6">
                                    {profile.awards.map((award, index) => (
                                    <div key={index} className="border border-zinc-800/40 rounded-lg p-6 space-y-4 relative bg-[#121214]">
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveAward(index)}
                                            className="absolute top-4 right-4 text-zinc-500 hover:text-red-500 transition-colors"
                                            >
                                                ×
                                            </button>
                                            <div>
                                            <Label className={`text-zinc-300 ${mono.className}`}>Award Title</Label>
                                            <Input
                                                    type="text"
                                                    value={award.title}
                                                    onChange={(e) => handleAwardChange(index, 'title', e.target.value)}
                                                className={`w-full bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                                />
                                            </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div>
                                                <Label className={`text-zinc-300 ${mono.className}`}>Grade Level</Label>
                                                <div className="space-y-2 mt-2">
                                                    {['9', '10', '11', '12', 'Post-graduate'].map((grade) => (
                                                        <label key={grade} className="flex items-center space-x-2">
                                                            <input
                                                                type="checkbox"
                                                                checked={award.grade_levels.includes(grade)}
                                                                onChange={(e) => {
                                                                    const newGrades = e.target.checked
                                                                        ? [...award.grade_levels, grade]
                                                                        : award.grade_levels.filter(g => g !== grade);
                                                                    handleAwardChange(index, 'grade_levels', newGrades);
                                                                }}
                                                                className="h-4 w-4 rounded border-zinc-800 bg-[#0A0A0B] text-[#E87C3E] focus:ring-[#E87C3E]"
                                                            />
                                                            <span className={`text-sm text-zinc-400 ${mono.className}`}>{grade}</span>
                                                        </label>
                                                    ))}
                                                </div>
                                            </div>
                                            <div>
                                                <Label className={`text-zinc-300 ${mono.className}`}>Level of Recognition</Label>
                                                <div className="space-y-2 mt-2">
                                                    {['School', 'State/Regional', 'National', 'International'].map((level) => (
                                                        <label key={level} className="flex items-center space-x-2">
                                                            <input
                                                                type="checkbox"
                                                                checked={award.recognition_levels.includes(level)}
                                                                onChange={(e) => {
                                                                    const newLevels = e.target.checked
                                                                        ? [...award.recognition_levels, level]
                                                                        : award.recognition_levels.filter(l => l !== level);
                                                                    handleAwardChange(index, 'recognition_levels', newLevels);
                                                                }}
                                                                className="h-4 w-4 rounded border-zinc-800 bg-[#0A0A0B] text-[#E87C3E] focus:ring-[#E87C3E]"
                                                            />
                                                            <span className={`text-sm text-zinc-400 ${mono.className}`}>{level}</span>
                                                        </label>
                                                    ))}
                                                </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                        </CardContent>
                    </Card>

                    {/* Hooks and Application Theme Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Hooks Section */}
                        <Card className="border-zinc-800/40 bg-[#0A0A0B]">
                            <CardHeader>
                                <CardTitle className={`text-white ${mono.className}`}>
                                    <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                                    Hooks
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                            <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>Personal Hooks</Label>
                                <select
                                    multiple
                                    value={profile?.hooks || []}
                                    onChange={(e) => {
                                        const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                                        setProfile(prev => ({
                                            ...prev,
                                            hooks: selectedOptions
                                        }));
                                    }}
                                        className={`w-full rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className} min-h-[160px]`}
                                >
                                    {HOOKS.map((hook) => (
                                            <option key={hook} value={hook} className={`p-2 hover:bg-[#E87C3E]/10`}>
                                            {hook}
                                        </option>
                                    ))}
                                </select>
                                    <p className={`text-sm text-zinc-400 mt-2 ${mono.className}`}>Hold Ctrl/Cmd to select multiple hooks</p>
                            </div>
                            </CardContent>
                        </Card>

                        {/* Application Theme Section */}
                        <Card className="border-zinc-800/40 bg-[#0A0A0B]">
                            <CardHeader>
                                <CardTitle className={`text-white ${mono.className}`}>
                                    <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                                    Application Theme
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>Personal Theme</Label>
                                    <textarea
                                        value={profile?.student_theme}
                                        onChange={(e) => setProfile({ ...profile, student_theme: e.target.value })}
                                        rows={6}
                                        className={`w-full rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className}`}
                                        placeholder="Describe your personal theme or story that connects your experiences"
                                    />
                        </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Student Preferences Section */}
                    <Card className="border-zinc-800/40 bg-[#0A0A0B]">
                        <CardHeader>
                            <CardTitle className={`text-white ${mono.className}`}>
                                <span className="inline-block w-1 h-4 bg-[#E87C3E] mr-2"></span>
                                College Preferences
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div>
                                <Label className={`text-zinc-300 mb-2 block ${mono.className}`}>Target Colleges</Label>
                                <div className="mt-3 space-y-4">
                                    <div className="flex gap-3">
                                        <div className="flex-1">
                                            <input
                                                type="text"
                                                placeholder="Enter college name"
                                                className={`w-full h-10 rounded-md bg-[#18181B] border-zinc-800/40 text-white placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-1 focus:ring-[#E87C3E] transition-colors ${mono.className}`}
                                                value={newCollegeName || ''}
                                                onChange={(e) => setNewCollegeName(e.target.value)}
                                            />
                                        </div>
                                        <div className="w-44">
                                            <select
                                                value={newCollegeType || ''}
                                                onChange={(e) => setNewCollegeType(e.target.value)}
                                                className={`w-full h-10 rounded-md bg-[#18181B] border-zinc-800/40 text-white placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-1 focus:ring-[#E87C3E] transition-colors ${mono.className}`}
                                            >
                                                <option value="" className="bg-[#18181B] text-zinc-600">Select Type</option>
                                                <option value="safety" className="bg-[#18181B] text-white">Safety</option>
                                                <option value="target" className="bg-[#18181B] text-white">Target</option>
                                                <option value="reach" className="bg-[#18181B] text-white">Reach</option>
                                            </select>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={handleAddCollege}
                                            className={`px-6 h-10 bg-[#E87C3E] text-white font-medium rounded-md hover:bg-[#FF8D4E] disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${mono.className}`}
                                            disabled={!newCollegeName || !newCollegeType}
                                        >
                                            Add
                                        </button>
                            </div>

                                    <div className="space-y-2.5 mt-4">
                                        {(profile?.target_colleges || []).map((college, index) => (
                                            <div 
                                                key={index} 
                                                className="flex items-center justify-between p-3 rounded-md bg-[#1A1A1A] border border-zinc-800/40 hover:border-zinc-700/40 transition-colors"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <span className={`text-white ${mono.className}`}>{college.name}</span>
                                                    <span className={`text-xs px-2.5 py-1 rounded-full ${
                                                        college.type === 'safety' ? 'bg-emerald-500/10 text-emerald-400' :
                                                        college.type === 'target' ? 'bg-blue-500/10 text-blue-400' :
                                                        'bg-amber-500/10 text-amber-400'
                                                    } ${mono.className}`}>
                                                        {college.type.charAt(0).toUpperCase() + college.type.slice(1)}
                                                    </span>
                                                </div>
                                                <button
                                                    type="button"
                                                    onClick={() => handleRemoveCollege(index)}
                                                    className="w-8 h-8 flex items-center justify-center text-zinc-500 hover:text-red-400 hover:bg-red-400/10 rounded-full transition-colors"
                                                    aria-label="Remove college"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                                    </svg>
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                            <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>Campus Sizes</Label>
                                <select
                                    multiple
                                    value={profile?.student_preferences?.campus_sizes || []}
                                    onChange={(e) => {
                                        const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                                        setProfile(prev => ({
                                            ...prev,
                                            student_preferences: {
                                                    ...prev.student_preferences,
                                                campus_sizes: selectedOptions
                                            }
                                        }));
                                    }}
                                        className={`w-full rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className} min-h-[120px]`}
                                >
                                        {['Small (<5,000)', 'Medium (5,000-15,000)', 'Large (>15,000)'].map((size) => (
                                            <option key={size} value={size} className="p-2 hover:bg-[#E87C3E]/10">
                                            {size}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>College Types</Label>
                                <select
                                    multiple
                                    value={profile?.student_preferences?.college_types || []}
                                    onChange={(e) => {
                                        const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                                        setProfile(prev => ({
                                            ...prev,
                                            student_preferences: {
                                                    ...prev.student_preferences,
                                                college_types: selectedOptions
                                            }
                                        }));
                                    }}
                                        className={`w-full rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className} min-h-[120px]`}
                                >
                                        {['Public', 'Private', 'Liberal Arts', 'Research University', 'Community College'].map((type) => (
                                            <option key={type} value={type} className="p-2 hover:bg-[#E87C3E]/10">
                                            {type}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>Preferred Regions</Label>
                                <select
                                    multiple
                                    value={profile?.student_preferences?.preferred_regions || []}
                                    onChange={(e) => {
                                        const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                                        setProfile(prev => ({
                                            ...prev,
                                            student_preferences: {
                                                    ...prev.student_preferences,
                                                preferred_regions: selectedOptions
                                            }
                                        }));
                                    }}
                                        className={`w-full rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className} min-h-[120px]`}
                                >
                                        {['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West Coast'].map((region) => (
                                            <option key={region} value={region} className="p-2 hover:bg-[#E87C3E]/10">
                                            {region}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                    <Label className={`text-zinc-300 ${mono.className}`}>Preferred States</Label>
                                <select
                                    multiple
                                    value={profile?.student_preferences?.preferred_states || []}
                                    onChange={(e) => {
                                        const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                                        setProfile(prev => ({
                                            ...prev,
                                            student_preferences: {
                                                    ...prev.student_preferences,
                                                preferred_states: selectedOptions
                                            }
                                        }));
                                    }}
                                        className={`w-full rounded-md bg-[#18181B] border-zinc-800/40 text-white focus:border-[#E87C3E] focus:ring-0 ${mono.className} min-h-[120px]`}
                                >
                                    {US_STATES.map((state) => (
                                            <option key={state} value={state} className="p-2 hover:bg-[#E87C3E]/10">
                                            {state}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        </CardContent>
                    </Card>

                    <Button
                        type="submit"
                        disabled={loading}
                        className={`w-full bg-[#E87C3E] hover:bg-[#FF8D4E] text-white ${mono.className} h-11 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#E87C3E]`}
                    >
                        {loading ? 'Saving...' : 'Save Profile'}
                    </Button>
                </form>
            </div>
        </div>
    );
} 