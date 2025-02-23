export const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL 
  ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api`
  : 'http://localhost:5000/api';

export const API_ENDPOINTS = {
    GENERATE_LIST: `${API_BASE_URL}/college-list`,
    CURRENT_SUGGESTIONS: `${API_BASE_URL}/college-list/current-suggestions`,
    PAST_SUGGESTIONS: `${API_BASE_URL}/college-list/past-suggestions`,
    TARGET_COLLEGES: `${API_BASE_URL}/college-list/target-colleges`,
    ADD_TARGET: `${API_BASE_URL}/college-list/add-target`,
}; 
