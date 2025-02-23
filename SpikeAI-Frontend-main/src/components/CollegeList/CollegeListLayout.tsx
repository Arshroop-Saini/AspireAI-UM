import React, { useState, useEffect } from 'react';
import { Grid, Typography, Box, Pagination, CircularProgress, Paper } from '@mui/material';
import { useAuth0 } from '@auth0/auth0-react';
import CollegeCard from './CollegeCard';
import { fetchWithAuth } from '../../utils/fetchWithAuth';
import { API_ENDPOINTS } from '../../utils/api';

interface College {
    name: string;
    type: string;
    added_at?: string;
}

interface PaginatedResponse {
    colleges?: College[];
    suggestions?: College[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
}

const CollegeListLayout: React.FC<{
    onAddCollege: (college: College, source: 'temp' | 'permanent') => void;
    refreshTrigger?: number;
}> = ({ onAddCollege, refreshTrigger = 0 }) => {
    const { getAccessTokenSilently } = useAuth0();
    const [pastSuggestions, setPastSuggestions] = useState<College[]>([]);
    const [currentSuggestions, setCurrentSuggestions] = useState<College[]>([]);
    const [targetColleges, setTargetColleges] = useState<College[]>([]);
    const [pastPage, setPastPage] = useState(1);
    const [targetPage, setTargetPage] = useState(1);
    const [pastTotalPages, setPastTotalPages] = useState(1);
    const [targetTotalPages, setTargetTotalPages] = useState(1);
    const [loading, setLoading] = useState(true);

    const fetchPastSuggestions = async (page: number) => {
        try {
            const token = await getAccessTokenSilently();
            const response = await fetchWithAuth(
                `${API_ENDPOINTS.PAST_SUGGESTIONS}?page=${page}&per_page=10`,
                token
            );
            const data: PaginatedResponse = await response.json();
            setPastSuggestions(data.suggestions || []);
            setPastTotalPages(data.total_pages);
        } catch (error) {
            console.error('Error fetching past suggestions:', error);
            setPastSuggestions([]);
        }
    };

    const fetchCurrentSuggestions = async () => {
        try {
            const token = await getAccessTokenSilently();
            const response = await fetchWithAuth(
                API_ENDPOINTS.CURRENT_SUGGESTIONS,
                token
            );
            const data: PaginatedResponse = await response.json();
            setCurrentSuggestions(data.suggestions || []);
        } catch (error) {
            console.error('Error fetching current suggestions:', error);
            setCurrentSuggestions([]);
        }
    };

    const fetchTargetColleges = async (page: number) => {
        try {
            const token = await getAccessTokenSilently();
            const response = await fetchWithAuth(
                `${API_ENDPOINTS.TARGET_COLLEGES}?page=${page}&per_page=10`,
                token
            );
            const data: PaginatedResponse = await response.json();
            setTargetColleges(data.colleges || []);
            setTargetTotalPages(data.total_pages);
        } catch (error) {
            console.error('Error fetching target colleges:', error);
            setTargetColleges([]);
        }
    };

    const fetchAllData = async () => {
        setLoading(true);
        await Promise.all([
            fetchPastSuggestions(pastPage),
            fetchCurrentSuggestions(),
            fetchTargetColleges(targetPage)
        ]);
        setLoading(false);
    };

    useEffect(() => {
        fetchAllData();
    }, [pastPage, targetPage, refreshTrigger]);

    const handlePastPageChange = (event: React.ChangeEvent<unknown>, value: number) => {
        setPastPage(value);
    };

    const handleTargetPageChange = (event: React.ChangeEvent<unknown>, value: number) => {
        setTargetPage(value);
    };

    const handleAddFromPast = (college: College) => {
        onAddCollege(college, 'permanent');
    };

    const handleAddFromCurrent = (college: College) => {
        onAddCollege(college, 'temp');
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Grid container spacing={3}>
            {/* Past Suggestions Column */}
            <Grid item xs={12} md={4}>
                <Paper elevation={2} sx={{ p: 3, height: '100%', minHeight: '600px', bgcolor: 'background.paper', borderRadius: 2 }}>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: 'text.primary' }}>
                        Past Suggestions
                    </Typography>
                    <Box sx={{ mt: 2, mb: 2 }}>
                        {pastSuggestions.length === 0 ? (
                            <Typography color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>
                                No past suggestions available
                            </Typography>
                        ) : (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                {pastSuggestions.map((college, index) => (
                                    <CollegeCard
                                        key={`past-${index}`}
                                        name={college.name}
                                        type={college.type}
                                        added_at={college.added_at}
                                        onAdd={() => handleAddFromPast(college)}
                                    />
                                ))}
                            </Box>
                        )}
                    </Box>
                    {pastSuggestions.length > 0 && (
                        <Box sx={{ mt: 'auto', pt: 2, display: 'flex', justifyContent: 'center' }}>
                            <Pagination
                                count={pastTotalPages}
                                page={pastPage}
                                onChange={handlePastPageChange}
                                color="primary"
                                size="small"
                            />
                        </Box>
                    )}
                </Paper>
            </Grid>

            {/* Current Suggestions Column */}
            <Grid item xs={12} md={4}>
                <Paper elevation={2} sx={{ p: 3, height: '100%', minHeight: '600px', bgcolor: 'background.paper', borderRadius: 2 }}>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: 'text.primary' }}>
                        Current Suggestions
                    </Typography>
                    <Box sx={{ mt: 2, mb: 2 }}>
                        {currentSuggestions.length === 0 ? (
                            <Typography color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>
                                No current suggestions. Click &quot;Generate New Suggestions&quot; to get started.
                            </Typography>
                        ) : (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                {currentSuggestions.map((college, index) => (
                                    <CollegeCard
                                        key={`current-${index}`}
                                        name={college.name}
                                        type={college.type}
                                        added_at={college.added_at}
                                        onAdd={() => handleAddFromCurrent(college)}
                                    />
                                ))}
                            </Box>
                        )}
                    </Box>
                </Paper>
            </Grid>

            {/* Target Colleges Column */}
            <Grid item xs={12} md={4}>
                <Paper elevation={2} sx={{ p: 3, height: '100%', minHeight: '600px', bgcolor: 'background.paper', borderRadius: 2 }}>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: 'text.primary' }}>
                        Your Target Colleges
                    </Typography>
                    <Box sx={{ mt: 2, mb: 2 }}>
                        {targetColleges.length === 0 ? (
                            <Typography color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>
                                No target colleges added yet
                            </Typography>
                        ) : (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                {targetColleges.map((college, index) => (
                                    <CollegeCard
                                        key={`target-${index}`}
                                        name={college.name}
                                        type={college.type}
                                        added_at={college.added_at}
                                        showAddButton={false}
                                    />
                                ))}
                            </Box>
                        )}
                    </Box>
                    {targetColleges.length > 0 && (
                        <Box sx={{ mt: 'auto', pt: 2, display: 'flex', justifyContent: 'center' }}>
                            <Pagination
                                count={targetTotalPages}
                                page={targetPage}
                                onChange={handleTargetPageChange}
                                color="primary"
                                size="small"
                            />
                        </Box>
                    )}
                </Paper>
            </Grid>
        </Grid>
    );
};

export default CollegeListLayout; 
