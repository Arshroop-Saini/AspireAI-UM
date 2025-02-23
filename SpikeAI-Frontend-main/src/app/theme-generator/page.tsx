import { FeaturePage } from '@/components/FeaturePage';

export default function ThemeGeneratorPage() {
    return (
        <FeaturePage
            title="Theme Generator"
            description="Generate personal themes for your application"
            endpoint="/theme-generator"
            buttonText="Generate Themes"
        />
    );
} 
