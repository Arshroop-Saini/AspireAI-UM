'use client';

import DashboardNav from '@/components/dashboard/DashboardNav';

export default function ProfileLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div>
            <DashboardNav />
            {/* Main content */}
            <main className="pt-16">{children}</main>
        </div>
    );
} 