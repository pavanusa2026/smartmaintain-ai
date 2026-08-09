import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
} from '@mui/material';
import { Add } from '@mui/icons-material';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { machinesApi } from '../api/client';
import DateField from '../components/DateField';
import { parseApiError } from '../utils/validation';

export default function AdminPage() {
  const [snackOpen, setSnackOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [form, setForm] = useState({
    name: '',
    type: 'motor',
    location: '',
    manufacturer: '',
    modelNumber: '',
    installationDate: '',
    productionLine: '',
  });
  const queryClient = useQueryClient();

  const createMachine = useMutation({
    mutationFn: (data: Record<string, unknown>) => machinesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['machines'] });
      setSnackOpen(true);
      setErrorMsg('');
      setForm({ name: '', type: 'motor', location: '', manufacturer: '', modelNumber: '', installationDate: '', productionLine: '' });
    },
    onError: (err) => setErrorMsg(parseApiError(err)),
  });

  const handleRegister = () => {
    setErrorMsg('');
    const payload = {
      ...form,
      installationDate: form.installationDate || undefined,
    };
    createMachine.mutate(payload);
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700 }} gutterBottom>Administration</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Register machines, configure settings, and manage system parameters
      </Typography>

      {errorMsg && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setErrorMsg('')}>{errorMsg}</Alert>}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Register New Machine</Typography>
              <TextField fullWidth label="Machine Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} margin="normal" required />
              <FormControl fullWidth margin="normal">
                <InputLabel>Type</InputLabel>
                <Select value={form.type} label="Type" onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  {['motor', 'pump', 'conveyor', 'cnc', 'compressor', 'oven', 'packaging'].map((t) => (
                    <MenuItem key={t} value={t} sx={{ textTransform: 'capitalize' }}>{t}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField fullWidth label="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} margin="normal" required />
              <TextField fullWidth label="Manufacturer" value={form.manufacturer} onChange={(e) => setForm({ ...form, manufacturer: e.target.value })} margin="normal" />
              <TextField fullWidth label="Model Number" value={form.modelNumber} onChange={(e) => setForm({ ...form, modelNumber: e.target.value })} margin="normal" />
              <DateField
                label="Installation Date"
                value={form.installationDate}
                onChange={(e) => setForm({ ...form, installationDate: e.target.value })}
              />
              <TextField fullWidth label="Production Line" value={form.productionLine} onChange={(e) => setForm({ ...form, productionLine: e.target.value })} margin="normal" />
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleRegister}
                disabled={!form.name.trim() || !form.location.trim() || createMachine.isPending}
                sx={{ mt: 2 }}
              >
                {createMachine.isPending ? 'Registering...' : 'Register Machine'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>System Configuration</Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                Running in local development mode with in-memory storage and local ML models.
              </Alert>
              {[
                ['Storage Backend', 'In-Memory (local)'],
                ['ML Model', 'Local Isolation Forest + Random Forest'],
                ['Model Version', '1.0.0-local'],
                ['AI Explanations', 'Local RAG (Bedrock-ready)'],
                ['Authentication', 'JWT (Cognito-ready)'],
                ['Anomaly Threshold', '65%'],
                ['Failure Threshold', '70%'],
              ].map(([label, value]) => (
                <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between', py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="body2" color="text.secondary">{label}</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>{value}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Demo Users</Typography>
              {[
                ['Admin', 'admin@smartmaintain.ai'],
                ['Supervisor', 'supervisor@smartmaintain.ai'],
                ['Technician', 'tech@smartmaintain.ai'],
                ['Operator', 'operator@smartmaintain.ai'],
                ['Inspector', 'inspector@smartmaintain.ai'],
              ].map(([role, email]) => (
                <Box key={email} sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                  <Typography variant="body2">{role}</Typography>
                  <Typography variant="body2" color="text.secondary">{email}</Typography>
                </Box>
              ))}
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                All demo accounts use password: demo123
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar open={snackOpen} autoHideDuration={3000} onClose={() => setSnackOpen(false)} message="Machine registered successfully" />
    </Box>
  );
}
