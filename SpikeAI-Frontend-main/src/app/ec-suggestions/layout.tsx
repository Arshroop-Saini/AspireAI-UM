'use client';

import DashboardNav from '@/components/dashboard/DashboardNav';

export default function ECRecommendationsLayout({
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