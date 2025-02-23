import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Modal,
  Box,
  IconButton,
  Button,
  Chip,
  Stack,
  Divider,
  Paper
} from '@mui/material';
import {
  School as SchoolIcon,
  Add as AddIcon,
  Close as CloseIcon,
  CalendarToday
} from '@mui/icons-material';

interface CollegeCardProps {
  name: string;
  type: string;
  added_at?: string;
  onAdd?: () => void;
  showAddButton?: boolean;
}

const modalStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '90%',
  maxWidth: 600,
  bgcolor: 'background.paper',
  boxShadow: 24,
  p: 4,
  borderRadius: 2,
  maxHeight: '90vh',
  overflow: 'auto'
};

export const CollegeCard: React.FC<CollegeCardProps> = ({ 
  name, 
  type,
  added_at,
  onAdd,
  showAddButton = true
}) => {
  const [modalOpen, setModalOpen] = useState(false);

  const handleAdd = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onAdd) {
      onAdd();
    }
  };

  return (
    <>
      <Card 
        onClick={() => setModalOpen(true)}
        sx={{
          cursor: 'pointer',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          '&:hover': {
            boxShadow: 6,
            transform: 'translateY(-2px)',
            transition: 'all 0.2s ease-in-out'
          }
        }}
      >
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SchoolIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
                {name}
              </Typography>
            </Box>
            {showAddButton && onAdd && (
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={handleAdd}
                size="small"
              >
                Add
              </Button>
            )}
          </Box>

          <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
            <Chip size="small" label={type} />
            {added_at && (
              <Chip size="small" label={new Date(added_at).toLocaleDateString()} icon={<CalendarToday />} />
            )}
          </Stack>
        </CardContent>
      </Card>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        aria-labelledby="college-details-modal"
      >
        <Paper sx={modalStyle}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h2">
              {name}
            </Typography>
            <IconButton onClick={() => setModalOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>

          <Divider sx={{ mb: 3 }} />

          <Box>
            <Typography variant="h6" gutterBottom>College Information</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <SchoolIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography>Type: {type}</Typography>
            </Box>
            {added_at && (
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CalendarToday sx={{ mr: 1, color: 'primary.main' }} />
                <Typography>Added: {new Date(added_at).toLocaleDateString()}</Typography>
              </Box>
            )}
          </Box>

          {showAddButton && onAdd && (
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAdd}
              >
                Add to My List
              </Button>
            </Box>
          )}
        </Paper>
      </Modal>
    </>
  );
}; 
