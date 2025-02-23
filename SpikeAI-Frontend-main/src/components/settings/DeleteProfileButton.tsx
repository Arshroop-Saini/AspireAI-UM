import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Trash2, Loader2 } from 'lucide-react';
import { useSession, signOut } from 'next-auth/react';
import { toast } from 'sonner';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

export function DeleteProfileButton() {
    const { data: session } = useSession();
    const [isDeleting, setIsDeleting] = useState(false);

    const handleDeleteProfile = async () => {
        if (!session?.id_token) {
            toast.error('You must be logged in to delete your profile');
            return;
        }

        try {
            setIsDeleting(true);
            toast.loading('Deleting your profile...', { id: 'delete-profile' });

            // First verify the session is still valid
            const verifyResponse = await fetch('/api/auth/verify-session', {
                headers: {
                    'Authorization': `Bearer ${session.id_token}`
                }
            });

            if (!verifyResponse.ok) {
                throw new Error('Session verification failed');
            }

            // Then proceed with deletion
            const response = await fetch('/api/profile/delete', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${session.id_token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            console.log('Delete profile response:', data);

            if (!response.ok) {
                throw new Error(data.error || 'Failed to delete profile');
            }

            toast.success('Your profile has been deleted successfully', { id: 'delete-profile' });
            
            // Sign out the user after successful deletion
            await signOut({ callbackUrl: '/auth/signin' });
        } catch (err) {
            console.error('Error deleting profile:', err);
            const errorMessage = err instanceof Error ? err.message : 'Failed to delete profile';
            toast.error(errorMessage, { id: 'delete-profile' });
            setIsDeleting(false);
        }
    };

    return (
        <AlertDialog>
            <AlertDialogTrigger asChild>
                <Button 
                    variant="outline"
                    className="w-full bg-red-600 hover:bg-red-700 text-white hover:text-white"
                    disabled={isDeleting}
                >
                    {isDeleting ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Deleting...
                        </>
                    ) : (
                        <>
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete Profile
                        </>
                    )}
                </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                        This action cannot be undone. This will permanently delete your profile
                        and remove all of your data from our servers, including:
                        <ul className="list-disc list-inside mt-2 space-y-1">
                            <li>Your personal information and preferences</li>
                            <li>Your subscription data</li>
                            <li>All generated college lists and recommendations</li>
                            <li>All stored memories and interactions</li>
                        </ul>
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                        onClick={handleDeleteProfile}
                        className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
                        disabled={isDeleting}
                    >
                        {isDeleting ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Deleting...
                            </>
                        ) : (
                            'Yes, delete my profile'
                        )}
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
} 