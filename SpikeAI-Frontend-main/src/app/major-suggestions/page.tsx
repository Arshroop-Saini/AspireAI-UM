import { FeaturePage } from '@/components/FeaturePage';

export default function MajorSuggestionsPage() {
    return (
        <FeaturePage
            title="Major Suggestions"
            description="Get personalized major recommendations"
            endpoint="/major-suggestions"
            buttonText="Get Suggestions"
        />
    );
} 
