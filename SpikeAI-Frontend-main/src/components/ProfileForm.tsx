import React, { useState, useEffect, ChangeEvent, FormEvent } from 'react';
import { Box, Grid, TextField, Button, Typography, Switch, FormControlLabel } from '@mui/material';
import ArrayFieldInput from './ArrayFieldInput';
import MultiSelect from './MultiSelect';
import { CAMPUS_SIZES, COLLEGE_TYPES, US_REGIONS, US_STATES } from '../constants/profileOptions';
import { useAuth0 } from '@auth0/auth0-react';

interface StudentContext {
  country: string;
  estimated_contribution: number;
  ethnicity: string;
  gender: string;
  financial_aid_required: boolean;
  first_generation: boolean;
  international_student: boolean;
}

interface StudentStatistics {
  class_rank: number;
  unweight_gpa: number;
  weight_gpa: number;
  sat_score: number;
}

interface StudentPreferences {
  campus_sizes: string[];
  college_types: string[];
  preferred_regions: string[];
  preferred_states: string[];
}

interface FormData {
  name: string;
  major: string;
  extracurriculars: string[];
  awards: string[];
  hooks: string[];
  target_colleges: string[];
  student_preferences: StudentPreferences;
  student_context: StudentContext;
  student_statistics: StudentStatistics;
  student_theme: string;
}

interface ProfileFormProps {
  onSubmit: (data: FormData & { auth0_id?: string; email?: string }) => void;
  initialData?: Partial<FormData>;
}

const ProfileForm: React.FC<ProfileFormProps> = ({ onSubmit, initialData }) => {
  const { user } = useAuth0();
  const [formData, setFormData] = useState<FormData>({
    name: '',
    major: '',
    extracurriculars: [],
    awards: [],
    hooks: [],
    target_colleges: [],
    student_preferences: {
      campus_sizes: [],
      college_types: [],
      preferred_regions: [],
      preferred_states: []
    },
    student_context: {
      country: '',
      estimated_contribution: 0,
      ethnicity: '',
      gender: '',
      financial_aid_required: false,
      first_generation: false,
      international_student: false
    },
    student_statistics: {
      class_rank: 0,
      unweight_gpa: 0,
      weight_gpa: 0,
      sat_score: 0
    },
    student_theme: ''
  });

  useEffect(() => {
    if (initialData) {
      setFormData(prev => ({ ...prev, ...initialData }));
    }
  }, [initialData]);

  const handleChange = (field: keyof FormData, value: FormData[keyof FormData]) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handlePreferenceChange = (field: keyof StudentPreferences, value: string[]) => {
    setFormData(prev => ({
      ...prev,
      student_preferences: {
        ...prev.student_preferences,
        [field]: value
      }
    }));
  };

  const handleContextChange = (field: keyof StudentContext, value: string | number | boolean) => {
    setFormData(prev => ({
      ...prev,
      student_context: {
        ...prev.student_context,
        [field]: value
      }
    }));
  };

  const handleStatisticsChange = (field: keyof StudentStatistics, value: number) => {
    setFormData(prev => ({
      ...prev,
      student_statistics: {
        ...prev.student_statistics,
        [field]: value
      }
    }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const data = {
      ...formData,
      auth0_id: user?.sub,
      email: user?.email
    };
    onSubmit(data);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Typography variant="h6">Basic Information</Typography>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleChange('name', e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Major"
            value={formData.major}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleChange('major', e.target.value)}
            margin="normal"
          />
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h6">Activities & Achievements</Typography>
          <ArrayFieldInput
            label="Extracurricular Activities"
            value={formData.extracurriculars}
            onChange={(value) => handleChange('extracurriculars', value)}
            placeholder="Add an activity"
          />
          <ArrayFieldInput
            label="Awards & Honors"
            value={formData.awards}
            onChange={(value) => handleChange('awards', value)}
            placeholder="Add an award"
          />
          <ArrayFieldInput
            label="Hooks"
            value={formData.hooks}
            onChange={(value) => handleChange('hooks', value)}
            placeholder="Add a hook"
          />
          <ArrayFieldInput
            label="Target Colleges"
            value={formData.target_colleges}
            onChange={(value) => handleChange('target_colleges', value)}
            placeholder="Add a target college"
          />
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h6">College Preferences</Typography>
          <MultiSelect
            label="Campus Sizes"
            value={formData.student_preferences.campus_sizes}
            options={CAMPUS_SIZES}
            onChange={(value) => handlePreferenceChange('campus_sizes', value)}
          />
          <MultiSelect
            label="College Types"
            value={formData.student_preferences.college_types}
            options={COLLEGE_TYPES}
            onChange={(value) => handlePreferenceChange('college_types', value)}
          />
          <MultiSelect
            label="Preferred Regions"
            value={formData.student_preferences.preferred_regions}
            options={US_REGIONS}
            onChange={(value) => handlePreferenceChange('preferred_regions', value)}
          />
          <MultiSelect
            label="Preferred States"
            value={formData.student_preferences.preferred_states}
            options={US_STATES}
            onChange={(value) => handlePreferenceChange('preferred_states', value)}
          />
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h6">Academic Information</Typography>
          <TextField
            fullWidth
            label="Class Rank"
            type="number"
            value={formData.student_statistics.class_rank}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleStatisticsChange('class_rank', Number(e.target.value))}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Unweighted GPA"
            type="number"
            value={formData.student_statistics.unweight_gpa}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleStatisticsChange('unweight_gpa', Number(e.target.value))}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Weighted GPA"
            type="number"
            value={formData.student_statistics.weight_gpa}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleStatisticsChange('weight_gpa', Number(e.target.value))}
            margin="normal"
          />
          <TextField
            fullWidth
            label="SAT Score"
            type="number"
            value={formData.student_statistics.sat_score}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleStatisticsChange('sat_score', Number(e.target.value))}
            margin="normal"
          />
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h6">Personal Information</Typography>
          <TextField
            fullWidth
            label="Country"
            value={formData.student_context.country}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleContextChange('country', e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Estimated Contribution"
            type="number"
            value={formData.student_context.estimated_contribution}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleContextChange('estimated_contribution', Number(e.target.value))}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Ethnicity"
            value={formData.student_context.ethnicity}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleContextChange('ethnicity', e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Gender"
            value={formData.student_context.gender}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleContextChange('gender', e.target.value)}
            margin="normal"
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.student_context.financial_aid_required}
                onChange={(e) => handleContextChange('financial_aid_required', e.target.checked)}
              />
            }
            label="Financial Aid Required"
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.student_context.first_generation}
                onChange={(e) => handleContextChange('first_generation', e.target.checked)}
              />
            }
            label="First Generation Student"
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.student_context.international_student}
                onChange={(e) => handleContextChange('international_student', e.target.checked)}
              />
            }
            label="International Student"
          />
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h6">Theme</Typography>
          <TextField
            fullWidth
            label="Student Theme"
            multiline
            rows={4}
            value={formData.student_theme}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleChange('student_theme', e.target.value)}
            margin="normal"
          />
        </Grid>

        <Grid item xs={12}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            size="large"
            fullWidth
          >
            Save Profile
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProfileForm; 
