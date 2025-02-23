'use client';

import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { signOut, useSession } from 'next-auth/react';
import Image from 'next/image';
import Link from 'next/link';
import { toast } from 'sonner';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export function UserMenu() {
  const { data: session } = useSession();

  const handleDeleteAccount = async () => {
    if (!session?.id_token) {
      toast.error('You must be logged in to delete your profile');
      return;
    }

    try {
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
        },
        body: JSON.stringify({})
      });

      const data = await response.json();
      console.log('Delete profile response:', data);

      if (!response.ok) {
        throw new Error(data.error || 'Failed to delete profile');
      }

      toast.success('Your profile has been deleted successfully');
      
      // Sign out the user after successful deletion
      await signOut({ callbackUrl: '/auth/signin' });
    } catch (err) {
      console.error('Error deleting profile:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete profile';
      toast.error(errorMessage);
    }
  };

  return (
    <Menu as="div" className="relative ml-3">
      <div>
        <Menu.Button className="relative flex rounded-full bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800">
          <span className="absolute -inset-1.5" />
          <span className="sr-only">Open user menu</span>
          <Image
            className="h-8 w-8 rounded-full"
            src={session?.user?.image || '/default-avatar.png'}
            alt="User avatar"
            width={32}
            height={32}
          />
        </Menu.Button>
      </div>
      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-dark-800 py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <Menu.Item>
            {({ active }) => (
              <Link
                href="/profile"
                className={classNames(
                  active ? 'bg-dark-700' : '',
                  'block px-4 py-2 text-sm text-gray-300'
                )}
              >
                Your Profile
              </Link>
            )}
          </Menu.Item>
          <Menu.Item>
            {({ active }) => (
              <Link
                href="/settings"
                className={classNames(
                  active ? 'bg-dark-700' : '',
                  'block px-4 py-2 text-sm text-gray-300'
                )}
              >
                Settings
              </Link>
            )}
          </Menu.Item>
          <Menu.Item>
            {({ active }) => (
              <Link
                href="/subscription"
                className={classNames(
                  active ? 'bg-dark-700' : '',
                  'block px-4 py-2 text-sm text-gray-300'
                )}
              >
                Subscriptions
              </Link>
            )}
          </Menu.Item>
          <Menu.Item>
            {({ active }) => (
              <button
                onClick={() => signOut()}
                className={classNames(
                  active ? 'bg-dark-700' : '',
                  'block w-full text-left px-4 py-2 text-sm text-gray-300'
                )}
              >
                Sign out
              </button>
            )}
          </Menu.Item>
          <Menu.Item>
            {({ active }) => (
              <button
                onClick={handleDeleteAccount}
                className={classNames(
                  active ? 'bg-dark-700' : '',
                  'block w-full text-left px-4 py-2 text-sm text-red-500'
                )}
              >
                Delete Account
              </button>
            )}
          </Menu.Item>
        </Menu.Items>
      </Transition>
    </Menu>
  );
} 