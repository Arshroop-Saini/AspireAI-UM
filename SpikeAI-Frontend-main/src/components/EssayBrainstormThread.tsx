import { format } from 'date-fns';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface EssayThread {
    thread_id: string;
    college_name: string;
    essay_prompt: string;
    word_limit: number;
    ideas: Array<{
        content: string;
        created_at: string;
    }>;
    created_at: string;
    updated_at: string;
    status: 'pending' | 'completed' | 'error';
}

interface EssayBrainstormThreadProps {
    thread: EssayThread;
}

export default function EssayBrainstormThread({ thread }: EssayBrainstormThreadProps) {
    return (
        <div className="relative flex-1 flex flex-col bg-[#000000]">
            {/* Thread Header */}
            <div className="sticky top-0 z-10 flex flex-col gap-1 bg-[#000000] px-4 py-2 border-b border-gray-800">
                <h2 className="text-base text-white">{thread.college_name}</h2>
                <p className="text-xs text-zinc-500">{format(new Date(thread.created_at), 'MMM d, yyyy h:mm a')}</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto">
                {/* Initial Prompt Message */}
                <div className="flex gap-4 px-4 py-6">
                    <Avatar className="h-8 w-8 shrink-0">
                        <AvatarFallback className="bg-[#E87C3E] text-white text-sm">Y</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                        <div className="text-sm text-zinc-500">Prompt:</div>
                        <div className="text-sm text-white mt-1 mb-4">{thread.essay_prompt}</div>
                        <div className="text-sm text-zinc-500">Word Limit:</div>
                        <div className="text-sm text-white mt-1">{thread.word_limit} words</div>
                        <div className="text-xs text-zinc-500 mt-2">
                            {format(new Date(thread.created_at), 'MMM d, yyyy h:mm a')}
                        </div>
                    </div>
                </div>

                {/* AI Responses */}
                {thread.ideas?.map((idea, index) => (
                    <div key={index} className="flex gap-4 px-4 py-6 border-t border-gray-800">
                        <Avatar className="h-8 w-8 shrink-0">
                            <AvatarFallback className="bg-blue-600 text-white text-sm">AI</AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                            <div className="text-sm text-white whitespace-pre-wrap">{idea.content}</div>
                            <div className="text-xs text-zinc-500 mt-2">
                                {format(new Date(idea.created_at), 'MMM d, yyyy h:mm a')}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
} 