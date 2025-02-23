'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { format } from 'date-fns';
import { JetBrains_Mono } from 'next/font/google';
import { PlusCircle, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@radix-ui/react-label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface EssayFeedbackForm {
    college_name: string;
    prompt: string;
    essay_text: string;
    feedback_questions: string[];
    word_limit: number;
}

interface EssayIdea {
    content: string;
    created_at: string;
}

interface EssayThread {
    thread_id: string;
    college_name: string;
    prompt: string;
    essay_text: string;
    word_count: number;
    word_limit: number;
    feedback_questions: string[];
    feedbacks: Array<{
        content: string;
        created_at: string;
        feedback_questions: string[];
    }>;
    created_at: string;
    updated_at: string;
    status: 'pending' | 'completed' | 'error';
    essay_prompt: string;
    ideas: EssayIdea[];
    severity: number;
}

interface RequestBody {
    college_name: string;
    prompt: string;
    essay_text: string;
    feedback_questions: string[];
    word_count: number;
    word_limit: number;
    is_new_thread: boolean;
    thread_id?: string;  // Optional for new threads
}

const mono = JetBrains_Mono({ subsets: ['latin'] });

export default function EssayFeedbackPage() {
    const { data: session } = useSession();
    const [isLoading, setIsLoading] = useState(false);
    const [threads, setThreads] = useState<EssayThread[]>([]);
    const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [threadFeedbackQuestion, setThreadFeedbackQuestion] = useState('');
    const [formData, setFormData] = useState<EssayFeedbackForm>({
        college_name: '',
        prompt: '',
        essay_text: '',
        feedback_questions: [''],
        word_limit: 0
    });

    useEffect(() => {
        if (session?.user) {
            fetchThreads();
        }
    }, [session]);

    const fetchThreads = async () => {
        try {
            const response = await fetch('/api/essay-feedback/threads');
            if (!response.ok) {
                throw new Error('Failed to fetch threads');
            }
            const data = await response.json();
            setThreads(data.threads || []);
        } catch (error) {
            console.error('Error fetching threads:', error);
        }
    };

    const handleInputChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
        field: keyof EssayFeedbackForm
    ) => {
        setFormData(prev => ({
            ...prev,
            [field]: e.target.value
        }));
    };

    const handleQuestionChange = (index: number, value: string) => {
        setFormData(prev => {
            const newQuestions = [...prev.feedback_questions];
            newQuestions[index] = value;
            return {
                ...prev,
                feedback_questions: newQuestions
            };
        });
    };

    const addQuestion = () => {
        setFormData(prev => ({
            ...prev,
            feedback_questions: [...prev.feedback_questions, '']
        }));
    };

    const removeQuestion = (index: number) => {
        setFormData(prev => ({
            ...prev,
            feedback_questions: prev.feedback_questions.filter((_, i) => i !== index)
        }));
    };

    const handleNewThread = () => {
        setSelectedThreadId(null);
        setFormData({
            college_name: '',
            prompt: '',
            essay_text: '',
            feedback_questions: [''],
            word_limit: 0
        });
    };

    const handleThreadSelect = async (threadId: string) => {
        try {
            setSelectedThreadId(threadId);
            setThreadFeedbackQuestion('');
            const thread = threads.find(t => t.thread_id === threadId);
            if (thread) {
                setFormData({
                    college_name: thread.college_name,
                    prompt: thread.prompt,
                    essay_text: thread.essay_text,
                    feedback_questions: thread.feedback_questions,
                    word_limit: thread.word_limit
                });
            }
        } catch (error) {
            console.error('Error selecting thread:', error);
        }
    };

    const handleDeleteThread = async (threadId: string) => {
        try {
            const response = await fetch(`/api/essay-feedback/threads?threadId=${threadId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete thread');
            }

            await fetchThreads();
            if (selectedThreadId === threadId) {
                handleNewThread();
            }
        } catch (error) {
            console.error('Error deleting thread:', error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        if (e) e.preventDefault();
        setIsLoading(true);
        let newThreadId: string | undefined = undefined;

        try {
            const wordCount = formData.essay_text.trim().split(/\s+/).length;
            
            // Validate required fields for new threads
            if (!selectedThreadId) {
                if (!formData.college_name.trim()) {
                    throw new Error('College name is required');
                }
                if (!formData.prompt.trim()) {
                    throw new Error('Essay prompt is required');
                }
                if (!formData.essay_text.trim()) {
                    throw new Error('Essay text is required');
                }
            }

            // If this is a new thread, create it first
            if (!selectedThreadId) {
                // Create new thread
                const createThreadResponse = await fetch('/api/essay-feedback/threads', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        college_name: formData.college_name,
                        prompt: formData.prompt,
                        essay_text: formData.essay_text,
                        word_count: wordCount,
                        word_limit: formData.word_limit
                    }),
                });

                const threadData = await createThreadResponse.json();
                
                if (!createThreadResponse.ok || !threadData.success) {
                    throw new Error(threadData.error || 'Failed to create thread');
                }

                newThreadId = threadData.thread_id;
                if (!newThreadId) {
                    throw new Error('No thread ID received from server');
                }

                // Refresh threads and set the new thread as selected
                await fetchThreads();
                setSelectedThreadId(newThreadId);

                // Keep current form data since it matches the new thread
                setFormData(prev => ({
                    ...prev,
                    feedback_questions: [''] // Reset only feedback questions
                }));
            }

            const threadIdToUse = selectedThreadId || newThreadId;
            if (!threadIdToUse) {
                throw new Error('No thread ID available');
            }

            // Now generate feedback for the thread
            const requestBody: RequestBody = {
                college_name: formData.college_name,
                prompt: formData.prompt,
                essay_text: formData.essay_text,
                feedback_questions: selectedThreadId 
                    ? threadFeedbackQuestion.trim() ? [threadFeedbackQuestion] : []
                    : formData.feedback_questions.filter(q => q.trim()),
                word_count: wordCount,
                word_limit: formData.word_limit,
                is_new_thread: false, // Always false since we've already created the thread
                thread_id: threadIdToUse
            };
            
            // Generate feedback
            const response = await fetch('/api/essay-feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to generate feedback');
            }

            // Refresh the threads list to get the latest feedback
            await fetchThreads();

            setIsLoading(false);
            setSuccess('Your essay feedback has been generated successfully.');
            
            // Clear the thread feedback question if we're in thread view
            if (selectedThreadId) {
                setThreadFeedbackQuestion('');
            }

            // Scroll to the bottom to show new feedback
            setTimeout(() => {
                const chatContainer = document.querySelector('.overflow-y-auto');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }, 100);

        } catch (error) {
            console.error('Error submitting essay:', error);
            setIsLoading(false);
            setSuccess(null);
            // You might want to show an error message to the user here
        }
    };

    if (!session) {
        return (
            <div className="container mx-auto p-4">
                <Alert>
                    <AlertDescription>
                        Please sign in to use the essay feedback feature.
                    </AlertDescription>
                </Alert>
            </div>
        );
    }

    return (
        <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
            <div className="w-80 border-r border-zinc-800/40 h-full bg-[#121214] p-4 space-y-4">
                <Button
                    onClick={handleNewThread}
                    variant="outline"
                    className={`w-full justify-start border-zinc-800/40 bg-[#18181B] hover:bg-[#121214] text-[#E87C3E] hover:text-[#FF8D4E] ${mono.className}`}
                >
                    <PlusCircle className="mr-2 h-4 w-4" />
                    New Essay
                </Button>

                <div className="space-y-2">
                    {threads.map((thread: EssayThread) => (
                        <div
                            key={thread.thread_id}
                            className={cn(
                                'p-3 rounded-lg cursor-pointer transition-all duration-200 group relative',
                                selectedThreadId === thread.thread_id 
                                    ? 'bg-[#18181B] border border-[#E87C3E]/20' 
                                    : 'hover:bg-[#18181B] border border-zinc-800/40'
                            )}
                            onClick={() => handleThreadSelect(thread.thread_id)}
                        >
                            <h3 className={`font-medium truncate pr-8 text-white ${mono.className}`}>{thread.college_name}</h3>
                            <p className={`text-sm text-zinc-400 truncate ${mono.className}`}>
                                {thread.prompt}
                            </p>
                            <p className={`text-xs text-zinc-500 mt-1 ${mono.className}`}>
                                {format(new Date(thread.created_at), 'PPp')}
                            </p>
                            
                            <Button
                                variant="ghost"
                                size="sm"
                                className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity p-0 h-8 w-8 hover:bg-red-500/10"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteThread(thread.thread_id);
                                }}
                            >
                                <Trash2 className="h-4 w-4 text-red-400 hover:text-red-300" />
                            </Button>
                        </div>
                    ))}
                </div>
            </div>
            <div className="flex-1 flex flex-col bg-[#0A0A0B]">
                {selectedThreadId ? (
                    <>
                        <div className="sticky top-0 z-10 flex flex-col gap-1 bg-[#121214] px-6 py-4 border-b border-zinc-800/40">
                            <h2 className={`text-lg text-white ${mono.className}`}>
                                {threads.find(t => t.thread_id === selectedThreadId)?.college_name}
                            </h2>
                            <p className={`text-sm text-zinc-400 ${mono.className}`}>
                                {threads.find(t => t.thread_id === selectedThreadId)?.prompt}
                            </p>
                            <p className={`text-xs text-zinc-500 ${mono.className}`}>
                                {threads.find(t => t.thread_id === selectedThreadId)?.created_at && 
                                 format(new Date(threads.find(t => t.thread_id === selectedThreadId)!.created_at), 'PPp')}
                            </p>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {threads.find(t => t.thread_id === selectedThreadId) && (
                                <div className="flex gap-4">
                                    <Avatar className="h-8 w-8">
                                        <AvatarFallback className={`bg-[#E87C3E] text-white text-sm ${mono.className}`}>
                                            Y
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1 space-y-4">
                                        <div className={`p-4 rounded-lg bg-[#121214] border border-zinc-800/40 text-white ${mono.className}`}>
                                            {threads.find(t => t.thread_id === selectedThreadId)?.essay_text}
                                        </div>
                                        <div className={`text-xs text-zinc-500 ${mono.className}`}>
                                            {threads.find(t => t.thread_id === selectedThreadId)?.word_count} words
                                        </div>
                                    </div>
                                </div>
                            )}

                            {threads.find(t => t.thread_id === selectedThreadId)?.feedbacks.map((feedback, index) => (
                                <div key={index} className="flex gap-4">
                                    <Avatar className="h-8 w-8">
                                        <AvatarFallback className={`bg-[#18181B] text-white text-sm ${mono.className}`}>
                                            AI
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1 space-y-4">
                                        <div className={`p-4 rounded-lg bg-[#121214] border border-zinc-800/40 text-white ${mono.className}`}>
                                            {feedback.content}
                                        </div>
                                        {feedback.feedback_questions && feedback.feedback_questions.length > 0 && (
                                            <div className="space-y-2">
                                                <p className={`text-sm text-zinc-400 ${mono.className}`}>Addressed Questions:</p>
                                                <ul className={`list-disc list-inside space-y-1 text-sm text-zinc-500 ${mono.className}`}>
                                                    {feedback.feedback_questions.map((question, qIndex) => (
                                                        <li key={qIndex}>{question}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        <div className={`text-xs text-zinc-500 ${mono.className}`}>
                                            {format(new Date(feedback.created_at), 'PPp')}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="p-4 bg-[#121214] border-t border-zinc-800/40">
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="thread_feedback_question" className={`text-sm text-zinc-300 ${mono.className}`}>
                                        Ask a specific question about your essay
                                    </Label>
                                    <Input
                                        id="thread_feedback_question"
                                        value={threadFeedbackQuestion}
                                        onChange={(e) => setThreadFeedbackQuestion(e.target.value)}
                                        placeholder="e.g., How can I make my introduction more engaging?"
                                        className={`h-11 bg-[#18181B] border-zinc-800/40 text-white ${mono.className} placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors hover:border-zinc-700`}
                                    />
                                </div>
                                <Button 
                                    onClick={handleSubmit} 
                                    disabled={isLoading}
                                    className={`w-full bg-[#E87C3E] hover:bg-[#FF8D4E] text-white ${mono.className} h-11 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#E87C3E]`}
                                >
                                    {isLoading ? 'Generating Feedback...' : 'Get New Feedback'}
                                </Button>
                            </div>
                        </div>
                    </>
                ) : (
            <div className="flex-1 p-6 overflow-y-auto">
                        <Card className="border border-zinc-800/40 bg-[#121214] shadow-xl">
                            <CardHeader className="space-y-2 pb-6">
                                <CardTitle className={`text-2xl text-white ${mono.className} tracking-tight`}>Essay Feedback</CardTitle>
                                <CardDescription className={`${mono.className} text-zinc-400 text-sm`}>
                            Get personalized feedback on your college application essay
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                                <form onSubmit={handleSubmit} className="space-y-8">
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <Label htmlFor="college_name" className={`text-sm text-zinc-300 ${mono.className}`}>College Name</Label>
                                <Input
                                    id="college_name"
                                    value={formData.college_name}
                                    onChange={(e) => handleInputChange(e, 'college_name')}
                                    placeholder="Enter college name"
                                    required
                                                className={`h-11 bg-[#18181B] border-zinc-800/40 text-white ${mono.className} placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors hover:border-zinc-700`}
                                />
                            </div>

                                        <div className="space-y-2">
                                            <Label htmlFor="prompt" className={`text-sm text-zinc-300 ${mono.className}`}>Essay Prompt</Label>
                                <Textarea
                                    id="prompt"
                                    value={formData.prompt}
                                    onChange={(e) => handleInputChange(e, 'prompt')}
                                    placeholder="Enter the essay prompt"
                                    required
                                                className={`min-h-[120px] resize-none bg-[#18181B] border-zinc-800/40 text-white ${mono.className} placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors hover:border-zinc-700`}
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <Label htmlFor="word_limit" className={`text-sm text-zinc-300 ${mono.className}`}>Word Limit</Label>
                                            <Input
                                                id="word_limit"
                                                type="number"
                                                min="0"
                                                value={formData.word_limit || ''}
                                                onChange={(e) => handleInputChange(e, 'word_limit')}
                                                placeholder="Enter maximum word limit"
                                                className={`h-11 bg-[#18181B] border-zinc-800/40 text-white ${mono.className} placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors hover:border-zinc-700`}
                                />
                            </div>

                                        <div className="space-y-2">
                                            <Label htmlFor="essay_text" className={`text-sm text-zinc-300 ${mono.className}`}>Essay Text</Label>
                                            <div className="relative">
                                <Textarea
                                    id="essay_text"
                                    value={formData.essay_text}
                                    onChange={(e) => handleInputChange(e, 'essay_text')}
                                    placeholder="Paste your essay here"
                                    required
                                                    className={`min-h-[250px] resize-none bg-[#18181B] border-zinc-800/40 text-white ${mono.className} placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors hover:border-zinc-700`}
                                />
                                                <div className={`absolute bottom-3 right-3 text-sm text-zinc-400 bg-[#121214] px-3 py-1.5 rounded-md border border-zinc-800/40 ${mono.className}`}>
                                                    {formData.essay_text.trim().split(/\s+/).filter(Boolean).length} / {formData.word_limit || '∞'} words
                                                </div>
                                            </div>
                            </div>

                                        <div className="space-y-4 pt-4">
                                            <Card className="p-5 bg-[#121214] border border-zinc-800/40">
                                                <CardHeader className="px-0 pt-0">
                                                    <CardTitle className={`text-lg text-white ${mono.className}`}>Feedback Questions</CardTitle>
                                                    <CardDescription className={`${mono.className} text-zinc-400 text-sm`}>
                                                        Add specific questions you&apos;d like the AI to address about your essay.
                                                        This helps get more targeted and relevant feedback.
                                                    </CardDescription>
                                                </CardHeader>
                                                <CardContent className="px-0 pb-0">
                                {formData.feedback_questions.map((question, index) => (
                                                        <div key={index} className="flex gap-3 mb-3">
                                        <Input
                                            value={question}
                                            onChange={(e) => handleQuestionChange(index, e.target.value)}
                                                                placeholder={index === 0 ? "e.g., How can I make my introduction more engaging?" : "Ask another specific question about your essay"}
                                                                className={`flex-1 h-11 bg-[#18181B] border-zinc-800/40 text-white ${mono.className} placeholder:text-zinc-600 focus:border-[#E87C3E] focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors hover:border-zinc-700`}
                                        />
                                        {index > 0 && (
                                            <Button
                                                type="button"
                                                variant="outline"
                                                onClick={() => removeQuestion(index)}
                                                                    className={`shrink-0 text-red-400 hover:text-red-300 border-zinc-800/40 hover:bg-red-500/10 ${mono.className} px-4`}
                                            >
                                                Remove
                                            </Button>
                                        )}
                                    </div>
                                ))}
                                                    <Button
                                                        type="button"
                                                        variant="outline"
                                                        onClick={addQuestion}
                                                        className={`mt-2 text-[#E87C3E] hover:text-[#FF8D4E] border-zinc-800/40 hover:bg-[#E87C3E]/10 ${mono.className}`}
                                                    >
                                                        <span className="mr-2">+</span> Add Question
                                </Button>
                                                </CardContent>
                                            </Card>
                                        </div>
                            </div>

                                    {success && (
                                        <Alert variant="default" className="bg-green-500/10 border-green-500/20">
                                            <AlertDescription className={`text-green-400 ${mono.className}`}>{success}</AlertDescription>
                                </Alert>
                            )}

                                    <Button 
                                        type="submit" 
                                        disabled={isLoading}
                                        className={`w-full bg-[#E87C3E] hover:bg-[#FF8D4E] text-white ${mono.className} h-11 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#E87C3E]`}
                                    >
                                        {isLoading ? 'Generating Feedback...' : 'Get Feedback'}
                            </Button>
                        </form>
                    </CardContent>
                </Card>
                    </div>
                )}
            </div>
        </div>
    );
} 