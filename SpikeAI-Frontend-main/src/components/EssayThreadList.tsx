import { Button } from '@/components/ui/button';
import { format } from 'date-fns';
import { PlusCircle, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

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

interface EssayThreadListProps {
    threads: EssayThread[];
    selectedThreadId: string | null;
    onThreadSelect: (threadId: string) => void;
    onNewThread: () => void;
    onDeleteThread: (threadId: string) => void;
}

export default function EssayThreadList({
    threads,
    selectedThreadId,
    onThreadSelect,
    onNewThread,
    onDeleteThread,
}: EssayThreadListProps) {
    return (
        <div className="w-80 border-r h-full p-4 space-y-4">
            <Button
                onClick={onNewThread}
                variant="outline"
                className="w-full justify-start"
            >
                <PlusCircle className="mr-2 h-4 w-4" />
                New Essay
            </Button>

            <div className="space-y-2">
                {threads.map((thread) => (
                    <div
                        key={thread.thread_id}
                        className={cn(
                            'p-3 rounded-lg cursor-pointer hover:bg-accent relative group',
                            selectedThreadId === thread.thread_id && 'bg-accent'
                        )}
                        onClick={() => onThreadSelect(thread.thread_id)}
                    >
                        <h3 className="font-medium truncate pr-8">{thread.college_name}</h3>
                        <p className="text-sm text-muted-foreground truncate">
                            {thread.essay_prompt}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                            {format(new Date(thread.created_at), 'PPp')}
                        </p>
                        
                        <Button
                            variant="ghost"
                            size="sm"
                            className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity p-0 h-8 w-8"
                            onClick={(e) => {
                                e.stopPropagation();
                                onDeleteThread(thread.thread_id);
                            }}
                        >
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                ))}
            </div>
        </div>
    );
} 