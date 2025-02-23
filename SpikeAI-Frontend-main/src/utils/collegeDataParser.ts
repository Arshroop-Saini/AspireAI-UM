interface ParsedCollege {
  name: string;
  type: string;
  added_at?: string;
}

interface ApiResponse {
  data?: {
    college_list?: string;
  };
  success: boolean;
  error?: string;
}

export interface ParsedResponse {
  colleges: ParsedCollege[];
  message?: string;
}

export const parseCollegeData = (apiResponse: string): ParsedResponse => {
  if (!apiResponse || typeof apiResponse !== 'string') {
    return {
      colleges: [],
      message: 'No college suggestions available.'
    };
  }

  // Split content into lines and filter out empty lines
  const lines = apiResponse.split('\n').map(line => line.trim()).filter(Boolean);
  
  const colleges: ParsedCollege[] = [];
  
  for (const line of lines) {
    // Match lines like "1. Harvard University | Reach"
    const collegeMatch = line.match(/^\d+\.\s*([^|]+)\s*\|\s*([^|]+)$/);
    if (collegeMatch) {
      const [, name, type] = collegeMatch;
      colleges.push({
        name: name.trim(),
        type: type.trim(),
        added_at: new Date().toISOString()
      });
      continue;
    }

    // Skip non-college lines
    if (line.toLowerCase().includes('new unique suggestions') || 
        line.toLowerCase().includes('available new matches') ||
        line.toLowerCase().includes('limited suggestions')) {
      continue;
    }
  }

  // Handle case where we get "LIMITED SUGGESTIONS" message
  if (apiResponse.includes('LIMITED SUGGESTIONS')) {
    return {
      colleges,
      message: 'Limited suggestions available. Consider adjusting your preferences to see more matches.'
    };
  }

  // Handle any notes at the end
  let message = '';
  if (apiResponse.includes('Note:')) {
    message = apiResponse.split('Note:')[1].trim();
  }

  return {
    colleges,
    message: message || undefined
  };
};

export const formatCollegeResponse = (response: ApiResponse): ParsedResponse => {
  if (!response?.data?.college_list) {
    return {
      colleges: [],
      message: 'No college suggestions available.'
    };
  }

  return parseCollegeData(response.data.college_list);
};