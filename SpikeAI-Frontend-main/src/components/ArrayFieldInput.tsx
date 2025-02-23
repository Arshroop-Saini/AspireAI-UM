import React, { useState, ChangeEvent, KeyboardEvent } from 'react';
import { TextField, Box, IconButton, List, ListItem } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

interface ArrayFieldInputProps {
  label: string;
  value: string[];
  onChange: (newValue: string[]) => void;
  placeholder?: string;
}

const ArrayFieldInput: React.FC<ArrayFieldInputProps> = ({
  label,
  value,
  onChange,
  placeholder
}) => {
  const [newItem, setNewItem] = useState('');

  const handleAdd = () => {
    if (newItem.trim()) {
      onChange([...value, newItem.trim()]);
      setNewItem('');
    }
  };

  const handleRemove = (index: number) => {
    const newValue = value.filter((_, i) => i !== index);
    onChange(newValue);
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
        <TextField
          fullWidth
          label={label}
          value={newItem}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setNewItem(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          size="small"
        />
        <IconButton 
          onClick={handleAdd}
          color="primary"
          sx={{ bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' } }}
        >
          <AddIcon />
        </IconButton>
      </Box>
      <List dense>
        {value.map((item, index) => (
          <ListItem
            key={index}
            secondaryAction={
              <IconButton edge="end" onClick={() => handleRemove(index)} size="small">
                <DeleteIcon />
              </IconButton>
            }
            sx={{ bgcolor: 'background.paper', mb: 0.5, borderRadius: 1 }}
          >
            {item}
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default ArrayFieldInput; 
