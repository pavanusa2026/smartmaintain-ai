import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Paper,
  Chip,
  Divider,
} from '@mui/material';
import { Send, SmartToy } from '@mui/icons-material';
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { assistantApi } from '../api/client';
import { parseApiError } from '../utils/validation';
import type { AssistantResponse } from '../types';

const suggestedQuestions = [
  'What should I inspect when motor vibration increases?',
  'How do I check cooling pump seals for leaks?',
  'What are the conveyor belt alignment steps?',
  'What lockout/tagout procedures are required?',
];

export default function AssistantPage() {
  const [question, setQuestion] = useState('');
  const [machineId, setMachineId] = useState('MOTOR-204');
  const [response, setResponse] = useState<AssistantResponse | null>(null);

  const query = useMutation({
    mutationFn: () => assistantApi.query(question, machineId).then((r) => r.data),
    onSuccess: (data) => setResponse(data),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) query.mutate();
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Maintenance Assistant
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Ask questions about equipment maintenance using approved documentation
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Machine ID (optional)"
              value={machineId}
              onChange={(e) => setMachineId(e.target.value)}
              margin="normal"
              size="small"
              sx={{ maxWidth: 300 }}
            />
            <TextField
              fullWidth
              label="Ask a maintenance question..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              margin="normal"
              multiline
              rows={3}
              required
            />
            <Button
              type="submit"
              variant="contained"
              startIcon={query.isPending ? <CircularProgress size={18} color="inherit" /> : <Send />}
              disabled={query.isPending || !question.trim()}
              sx={{ mt: 1 }}
            >
              Ask Assistant
            </Button>
          </Box>

          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {suggestedQuestions.map((q) => (
              <Chip
                key={q}
                label={q}
                variant="outlined"
                size="small"
                onClick={() => { setQuestion(q); }}
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Box>
        </CardContent>
      </Card>

      {query.isError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => query.reset()}>
          {parseApiError(query.error)}
        </Alert>
      )}

      {response && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <SmartToy color="primary" />
              <Typography variant="h6">Assistant Response</Typography>
            </Box>

            <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {response.answer}
              </Typography>
            </Paper>

            <Alert severity="warning" sx={{ mb: 2 }}>
              {response.safetyNotice}
            </Alert>

            <Typography variant="subtitle2" gutterBottom>Sources</Typography>
            {(response.sources ?? []).map((src, i) => (
              <Paper key={i} variant="outlined" sx={{ p: 1.5, mb: 1 }}>
                <Typography variant="body2" fontWeight={600}>{src.title}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {src.section} · Rev. {src.revisionDate}
                </Typography>
              </Paper>
            ))}

            <Divider sx={{ my: 2 }} />
            <Typography variant="caption" color="text.secondary" fontStyle="italic">
              {response.humanReviewReminder}
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
