import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Paper,
} from '@mui/material';
import { PrecisionManufacturing } from '@mui/icons-material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { validateEmail, validatePassword, parseApiError } from '../utils/validation';

const demoAccounts = [
  { email: 'admin@smartmaintain.ai', role: 'Admin' },
  { email: 'supervisor@smartmaintain.ai', role: 'Supervisor' },
  { email: 'tech@smartmaintain.ai', role: 'Technician' },
  { email: 'operator@smartmaintain.ai', role: 'Operator' },
];

export default function LoginPage() {
  const [email, setEmail] = useState('supervisor@smartmaintain.ai');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    const emailErr = validateEmail(email);
    const passErr = validatePassword(password);
    if (emailErr) errors.email = emailErr;
    if (passErr) errors.password = passErr;
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!validate()) return;
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigate('/');
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAccount = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('demo123');
    setFieldErrors({});
    setError('');
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0d47a1 0%, #00695c 50%, #00838f 100%)',
        p: 2,
      }}
    >
      <Card sx={{ maxWidth: 440, width: '100%' }}>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <PrecisionManufacturing sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="h5" sx={{ fontWeight: 700 }}>SmartMaintain AI</Typography>
            <Typography variant="body2" color="text.secondary">
              Predictive Maintenance & Quality Monitoring
            </Typography>
          </Box>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Box component="form" onSubmit={handleSubmit} noValidate>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setFieldErrors((p) => ({ ...p, email: '' })); }}
              margin="normal"
              error={!!fieldErrors.email}
              helperText={fieldErrors.email}
              autoComplete="email"
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              placeholder="Enter demo123"
              onChange={(e) => { setPassword(e.target.value); setFieldErrors((p) => ({ ...p, password: '' })); }}
              margin="normal"
              error={!!fieldErrors.password}
              helperText={fieldErrors.password || 'Demo password: demo123'}
              autoComplete="current-password"
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading}
              sx={{ mt: 2, py: 1.5, minHeight: 48 }}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
            </Button>
          </Box>

          <Paper variant="outlined" sx={{ mt: 3, p: 2, bgcolor: 'grey.50' }}>
            <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
              Click a demo account to fill credentials
            </Typography>
            {demoAccounts.map((acc) => (
              <Typography
                key={acc.email}
                variant="caption"
                display="block"
                sx={{ cursor: 'pointer', py: 0.25, '&:hover': { color: 'primary.main' } }}
                onClick={() => fillDemoAccount(acc.email)}
              >
                {acc.role}: {acc.email}
              </Typography>
            ))}
          </Paper>
        </CardContent>
      </Card>
    </Box>
  );
}
