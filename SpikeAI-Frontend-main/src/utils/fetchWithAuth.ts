interface FetchOptions extends RequestInit {
    token?: string;
}

export const fetchWithAuth = async (url: string, token: string, options: FetchOptions = {}) => {
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;
}; 