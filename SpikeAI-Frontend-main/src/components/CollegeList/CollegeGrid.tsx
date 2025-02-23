import React from 'react';
import { Grid, Container, Typography, Box, Paper, Alert, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import CollegeCard from './CollegeCard';
import { School as SchoolIcon, ArrowRight as ArrowRightIcon } from '@mui/icons-material';

interface CollegeData {
  name: string;
  type: string;
  added_at?: string;
}

interface CollegeGridProps {
  colleges: CollegeData[];
  message?: string;
  isLimited?: boolean;
  suggestions?: string[];
}

const CollegeGrid: React.FC<CollegeGridProps> = ({ colleges, message, isLimited, suggestions }) => {
  const renderMessage = () => {
    if (!message) return null;

    return (
      <Alert 
        severity={isLimited ? "warning" : "info"} 
        sx={{ 
          mb: 4,
          '& .MuiAlert-message': {
            width: '100%'
          }
        }}
      >
        <Typography variant="subtitle1" gutterBottom>
          {message}
        </Typography>
        {suggestions && suggestions.length > 0 && (
          <List dense>
            {suggestions.map((suggestion, index) => (
              <ListItem key={index} sx={{ py: 0 }}>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <ArrowRightIcon color="action" />
                </ListItemIcon>
                <ListItemText primary={suggestion} />
              </ListItem>
            ))}
          </List>
        )}
      </Alert>
    );
  };

  if (!colleges || colleges.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {renderMessage()}
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Paper 
            elevation={0} 
            sx={{ 
              p: 4, 
              maxWidth: 600, 
              mx: 'auto',
              bgcolor: 'grey.50',
              borderRadius: 2
            }}
          >
            <SchoolIcon sx={{ fontSize: 60, color: 'grey.400', mb: 2 }} />
            <Typography variant="h5" color="text.secondary" gutterBottom>
              No Colleges Found
            </Typography>
            <Typography color="text.secondary">
              Try adjusting your preferences to see more college suggestions.
            </Typography>
          </Paper>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {renderMessage()}
      
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center' }}>
        <SchoolIcon sx={{ mr: 2, color: 'primary.main', fontSize: 40 }} />
        <Typography variant="h4" component="h1">
          Your College Matches
        </Typography>
      </Box>
      
      <Grid container spacing={3}>
        {colleges.map((college, index) => (
          <Grid item xs={12} sm={6} lg={4} key={index}>
            <CollegeCard 
              name={college.name} 
              type={college.type}
              added_at={college.added_at}
            />
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default CollegeGrid; 
