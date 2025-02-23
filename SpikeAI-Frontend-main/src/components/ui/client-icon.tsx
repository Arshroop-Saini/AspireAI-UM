import { LucideIcon } from "lucide-react";

interface IconProps {
    icon: LucideIcon;
}

export function ClientIcon({ icon: Icon }: IconProps) {
    return <Icon className="h-4 w-4" />;
} 