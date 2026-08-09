import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
} from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useRef } from 'react';
import { inspectionsApi } from '../api/client';
import StatusChip from '../components/StatusChip';
import type { Inspection } from '../types';

export default function InspectionsPage() {
  const [uploading, setUploading] = useState(false);
  const [lastResult, setLastResult] = useState<Inspection | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: inspections, isLoading, error } = useQuery({
    queryKey: ['inspections'],
    queryFn: () => inspectionsApi.list().then((r) => r.data),
  });

  const review = useMutation({
    mutationFn: ({ id, result }: { id: string; result: string }) =>
      inspectionsApi.review(id, { reviewedResult: result, reviewedBy: 'Inspector' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inspections'] }),
  });

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const { data } = await inspectionsApi.upload(file);
      setLastResult(data);
      queryClient.invalidateQueries({ queryKey: ['inspections'] });
    } catch {
      alert('Upload failed');
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  if (error) return <Alert severity="error">Failed to load inspections</Alert>;

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Quality Inspection
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Upload product images for AI-powered defect detection
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={handleUpload} />
          <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>Upload Product Image</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Supported formats: JPG, PNG, WebP (max 10MB)
          </Typography>
          <Button
            variant="contained"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? <CircularProgress size={24} /> : 'Select Image'}
          </Button>
        </CardContent>
      </Card>

      {lastResult && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Latest Analysis Result</Typography>
            <Box sx={{ display: 'flex', gap: 3, alignItems: 'center', flexWrap: 'wrap' }}>
              <Box>
                <Typography variant="body2" color="text.secondary">Prediction</Typography>
                <StatusChip status={lastResult.predictedResult} size="medium" />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Defect Type</Typography>
                <Typography variant="body1" sx={{ textTransform: 'capitalize' }}>
                  {lastResult.defectType.replace(/_/g, ' ')}
                </Typography>
              </Box>
              <Box sx={{ flex: 1, minWidth: 200 }}>
                <Typography variant="body2" color="text.secondary">Confidence</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={lastResult.confidence * 100}
                    sx={{ flex: 1, height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="body2">{Math.round(lastResult.confidence * 100)}%</Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button size="small" variant="outlined" color="success" onClick={() => review.mutate({ id: lastResult.inspectionId, result: lastResult.predictedResult })}>
                  Confirm
                </Button>
                <Button size="small" variant="outlined" onClick={() => review.mutate({ id: lastResult.inspectionId, result: lastResult.predictedResult === 'pass' ? 'fail' : 'pass' })}>
                  Override
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Inspection History</Typography>
          {isLoading ? (
            <CircularProgress />
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Product ID</TableCell>
                    <TableCell>Result</TableCell>
                    <TableCell>Defect</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Reviewed</TableCell>
                    <TableCell>Date</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(inspections as Inspection[])?.map((insp) => (
                    <TableRow key={insp.inspectionId}>
                      <TableCell>{insp.productId}</TableCell>
                      <TableCell><StatusChip status={insp.predictedResult} /></TableCell>
                      <TableCell sx={{ textTransform: 'capitalize' }}>{insp.defectType.replace(/_/g, ' ')}</TableCell>
                      <TableCell>{Math.round(insp.confidence * 100)}%</TableCell>
                      <TableCell>{insp.reviewedResult ? <StatusChip status={insp.reviewedResult} /> : '—'}</TableCell>
                      <TableCell><Typography variant="caption">{new Date(insp.createdAt).toLocaleString()}</Typography></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
