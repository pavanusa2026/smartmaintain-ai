import {
  Box,
  Card,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Alert as MuiAlert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { alertsApi, workOrdersApi } from '../api/client';
import StatusChip from '../components/StatusChip';
import FilterSelect, { filterValueToParam } from '../components/FilterSelect';
import { ErrorState, EmptyState } from '../components/StateViews';
import { parseApiError } from '../utils/validation';
import type { Alert as AlertRecord } from '../types';

const SEVERITY_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const STATUS_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'new', label: 'New' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'investigating', label: 'Investigating' },
  { value: 'closed', label: 'Closed' },
];

export default function AlertsPage() {
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedAlert, setSelectedAlert] = useState<AlertRecord | null>(null);
  const [woDialogOpen, setWoDialogOpen] = useState(false);
  const [woTitle, setWoTitle] = useState('');
  const [actionError, setActionError] = useState('');
  const queryClient = useQueryClient();

  const { data: alerts, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['alerts', severityFilter, statusFilter],
    queryFn: () =>
      alertsApi
        .list({
          severity: filterValueToParam(severityFilter),
          status: filterValueToParam(statusFilter),
        })
        .then((r) => r.data as AlertRecord[]),
    refetchInterval: 10000,
  });

  const acknowledge = useMutation({
    mutationFn: (id: string) => alertsApi.acknowledge(id),
    onSuccess: () => { setActionError(''); queryClient.invalidateQueries({ queryKey: ['alerts'] }); },
    onError: (err) => setActionError(parseApiError(err)),
  });

  const closeAlert = useMutation({
    mutationFn: (id: string) => alertsApi.update(id, { status: 'closed' }),
    onSuccess: () => { setActionError(''); queryClient.invalidateQueries({ queryKey: ['alerts'] }); },
    onError: (err) => setActionError(parseApiError(err)),
  });

  const createWorkOrder = useMutation({
    mutationFn: (data: Record<string, unknown>) => workOrdersApi.create(data),
    onSuccess: () => {
      setActionError('');
      queryClient.invalidateQueries({ queryKey: ['work-orders'] });
      setWoDialogOpen(false);
    },
    onError: (err) => setActionError(parseApiError(err)),
  });

  const handleCreateWO = () => {
    if (!selectedAlert) return;
    createWorkOrder.mutate({
      machineId: selectedAlert.machineId,
      alertId: selectedAlert.alertId,
      title: woTitle || selectedAlert.title,
      description: selectedAlert.explanation,
      priority: selectedAlert.severity === 'critical' ? 'emergency' : selectedAlert.severity === 'high' ? 'high' : 'normal',
    });
  };

  const alertList = alerts ?? [];

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 700 }} gutterBottom>Alerts</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Monitor, acknowledge, and respond to equipment alerts
      </Typography>

      {actionError && (
        <MuiAlert severity="error" sx={{ mb: 2 }} onClose={() => setActionError('')}>{actionError}</MuiAlert>
      )}

      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <FilterSelect label="Severity" value={severityFilter} options={SEVERITY_OPTIONS} onChange={setSeverityFilter} />
        <FilterSelect label="Status" value={statusFilter} options={STATUS_OPTIONS} onChange={setStatusFilter} />
      </Box>

      <Card>
        {isLoading ? (
          <Box sx={{ p: 4, textAlign: 'center' }}><CircularProgress /></Box>
        ) : isError ? (
          <Box sx={{ p: 2 }}><ErrorState message={parseApiError(error)} onRetry={() => refetch()} /></Box>
        ) : alertList.length === 0 ? (
          <EmptyState title="No alerts found" description="Try changing your filters or check back later." />
        ) : (
          <TableContainer sx={{ overflowX: 'auto' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Alert</TableCell>
                  <TableCell>Machine</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {alertList.map((alert) => (
                  <TableRow key={alert.alertId} hover>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>{alert.title}</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {alert.explanation}
                      </Typography>
                    </TableCell>
                    <TableCell>{alert.machineId}</TableCell>
                    <TableCell><StatusChip status={alert.severity} /></TableCell>
                    <TableCell sx={{ textTransform: 'capitalize' }}>{(alert.alertType || '').replace(/_/g, ' ')}</TableCell>
                    <TableCell><StatusChip status={alert.status} /></TableCell>
                    <TableCell>{Math.round((alert.confidence ?? 0) * 100)}%</TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {alert.createdAt ? new Date(alert.createdAt).toLocaleString() : '—'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {alert.status === 'new' && (
                          <Button size="small" onClick={() => acknowledge.mutate(alert.alertId)} disabled={acknowledge.isPending}>
                            Ack
                          </Button>
                        )}
                        {alert.status !== 'closed' && (
                          <>
                            <Button size="small" onClick={() => { setSelectedAlert(alert); setWoTitle(alert.title); setWoDialogOpen(true); }}>
                              WO
                            </Button>
                            <Button size="small" color="inherit" onClick={() => closeAlert.mutate(alert.alertId)} disabled={closeAlert.isPending}>
                              Close
                            </Button>
                          </>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>

      <Dialog open={woDialogOpen} onClose={() => setWoDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Work Order from Alert</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Title" value={woTitle} onChange={(e) => setWoTitle(e.target.value)} margin="normal" />
          {selectedAlert && (
            <MuiAlert severity="info" sx={{ mt: 1 }}>
              {selectedAlert.recommendedAction || 'Review alert details before creating work order.'}
            </MuiAlert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setWoDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateWO} disabled={createWorkOrder.isPending}>
            Create Work Order
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
