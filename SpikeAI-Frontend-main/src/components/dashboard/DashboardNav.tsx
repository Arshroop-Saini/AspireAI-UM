'use client';

import { UserMenu } from '@/components/dashboard/UserMenu';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { JetBrains_Mono } from 'next/font/google';
import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';

const mono = JetBrains_Mono({ 
    subsets: ['latin'],
    variable: '--font-mono'
});

export default function DashboardNav() {
    const pathname = usePathname();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Close mobile menu when route changes
    useEffect(() => {
        setIsMobileMenuOpen(false);
    }, [pathname]);

    const navItems = [
        { name: 'Dashboard', href: '/dashboard' },
        { name: 'College List', href: '/college-list' },
        { name: 'EC Suggestions', href: '/ec-suggestions' },
        { name: 'Essay Feedback', href: '/essay-feedback' },
        { name: 'Essay Brainstorm', href: '/essay-brainstorm' },
        { name: 'Profile', href: '/profile' }
    ];

    const toggleMobileMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen);
    };

    return (
        <nav className={`fixed top-0 left-0 right-0 z-50 ${mono.className}`}>
            {/* Main navbar */}
            <div className="bg-gradient-to-b from-black/90 via-black/80 to-transparent backdrop-blur-sm">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 items-center justify-between">
                        <div className="flex-shrink-0">
                            <h1 className="text-white text-xl">AspireAI</h1>
                        </div>
                        
                        {/* Desktop Menu */}
                        <div className="hidden md:flex flex-1 items-center justify-center px-8">
                            <div className="flex items-baseline space-x-4">
                                {navItems.map((item) => {
                                    const isActive = pathname === item.href;
                                    return (
                                        <Link
                                            key={item.name}
                                            href={item.href}
                                            className={`${
                                                isActive
                                                    ? 'bg-[#E87C3E] text-white'
                                                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                                            } rounded-md px-3 py-2 text-sm transition-colors duration-200`}
                                        >
                                            {item.name}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Desktop User Menu */}
                        <div className="hidden md:block">
                            <UserMenu />
                        </div>

                        {/* Mobile Menu Button */}
                        <div className="flex md:hidden">
                            <button
                                onClick={toggleMobileMenu}
                                className="text-gray-400 hover:text-white p-2 rounded-md transition-colors duration-200"
                                aria-label="Toggle menu"
                            >
                                {isMobileMenuOpen ? (
                                    <X className="h-6 w-6" />
                                ) : (
                                    <Menu className="h-6 w-6" />
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Mobile Menu */}
            <div 
                className={`${
                    isMobileMenuOpen ? 'translate-x-0 opacity-100' : '-translate-x-full opacity-0'
                } md:hidden fixed inset-0 z-40 transform transition-all duration-300 ease-in-out`}
            >
                {/* Backdrop */}
                <div 
                    className={`${
                        isMobileMenuOpen ? 'opacity-100' : 'opacity-0'
                    } fixed inset-0 bg-black/95 backdrop-blur-sm transition-opacity duration-300`}
                    onClick={() => setIsMobileMenuOpen(false)}
                />
                
                {/* Menu Content */}
                <div className="relative bg-black/95 h-full w-64 shadow-xl">
                    <div className="flex flex-col h-full pt-20 pb-6">
                        <div className="px-4 space-y-1">
                            {navItems.map((item) => {
                                const isActive = pathname === item.href;
                                return (
                                    <Link
                                        key={item.name}
                                        href={item.href}
                                        className={`${
                                            isActive
                                                ? 'bg-[#E87C3E] text-white'
                                                : 'text-gray-400 hover:text-white hover:bg-gray-800'
                                        } block rounded-md px-3 py-2 text-base font-medium transition-colors duration-200`}
                                    >
                                        {item.name}
                                    </Link>
                                );
                            })}
                        </div>
                        <div className="mt-auto px-4 pt-4 border-t border-gray-800">
                            <UserMenu />
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
} 
