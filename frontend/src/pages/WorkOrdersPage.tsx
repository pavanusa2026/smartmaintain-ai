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
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import { Add } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { workOrdersApi } from '../api/client';
import StatusChip from '../components/StatusChip';
import DateField from '../components/DateField';
import FilterSelect, { filterValueToParam } from '../components/FilterSelect';
import { ErrorState, EmptyState } from '../components/StateViews';
import { parseApiError } from '../utils/validation';
import type { WorkOrder } from '../types';

const STATUS_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'canceled', label: 'Canceled' },
];

export default function WorkOrdersPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [actionError, setActionError] = useState('');
  const [form, setForm] = useState({
    machineId: 'MOTOR-204',
    title: '',
    description: '',
    priority: 'normal',
    assignedTo: '',
    dueDate: '',
  });
  const queryClient = useQueryClient();

  const { data: workOrders, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['work-orders', statusFilter],
    queryFn: () =>
      workOrdersApi.list({ status: filterValueToParam(statusFilter) }).then((r) => r.data),
    refetchInterval: 10000,
  });

  const createWO = useMutation({
    mutationFn: (data: Record<string, unknown>) => workOrdersApi.create(data),
    onSuccess: () => {
      setActionError('');
      queryClient.invalidateQueries({ queryKey: ['work-orders'] });
      setCreateOpen(false);
      setForm({ machineId: 'MOTOR-204', title: '', description: '', priority: 'normal', assignedTo: '', dueDate: '' });
    },
    onError: (err) => setActionError(parseApiError(err)),
  });

  const updateWO = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      workOrdersApi.update(id, data),
    onSuccess: () => { setActionError(''); queryClient.invalidateQueries({ queryKey: ['work-orders'] }); },
    onError: (err) => setActionError(parseApiError(err)),
  });

  const woList = (workOrders as WorkOrder[] | undefined) ?? [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight={700}>Work Orders</Typography>
          <Typography variant="body2" color="text.secondary">Manage maintenance tasks and repairs</Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setCreateOpen(true)}>
          New Work Order
        </Button>
      </Box>

      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setActionError('')}>{actionError}</Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <FilterSelect label="Status" value={statusFilter} options={STATUS_OPTIONS} onChange={setStatusFilter} />
      </Box>

      <Card>
        {isLoading ? (
          <Box sx={{ p: 4, textAlign: 'center' }}><CircularProgress /></Box>
        ) : isError ? (
          <Box sx={{ p: 2 }}><ErrorState message={parseApiError(error)} onRetry={() => refetch()} /></Box>
        ) : woList.length === 0 ? (
          <EmptyState title="No work orders found" description="Create a new work order or adjust filters." />
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Title</TableCell>
                  <TableCell>Machine</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Assigned To</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {woList.map((wo) => (
                  <TableRow key={wo.workOrderId} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>{wo.title}</Typography>
                      <Typography variant="caption" color="text.secondary">{wo.workOrderId}</Typography>
                    </TableCell>
                    <TableCell>{wo.machineId}</TableCell>
                    <TableCell><StatusChip status={wo.priority} /></TableCell>
                    <TableCell><StatusChip status={wo.status} /></TableCell>
                    <TableCell>{wo.assignedTo || '—'}</TableCell>
                    <TableCell>{wo.dueDate || '—'}</TableCell>
                    <TableCell>
                      {wo.status === 'open' && (
                        <Button size="small" onClick={() => updateWO.mutate({ id: wo.workOrderId, data: { status: 'in_progress' } })}>
                          Start
                        </Button>
                      )}
                      {wo.status === 'in_progress' && (
                        <Button size="small" color="success" onClick={() => updateWO.mutate({ id: wo.workOrderId, data: { status: 'completed', resolutionNotes: 'Maintenance completed successfully.' } })}>
                          Complete
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Work Order</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Machine ID" value={form.machineId} onChange={(e) => setForm({ ...form, machineId: e.target.value })} margin="normal" />
          <TextField fullWidth label="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} margin="normal" required />
          <TextField fullWidth label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} margin="normal" multiline rows={3} />
          <FormControl fullWidth margin="normal">
            <InputLabel>Priority</InputLabel>
            <Select value={form.priority} label="Priority" onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="normal">Normal</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="emergency">Emergency</MenuItem>
            </Select>
          </FormControl>
          <TextField fullWidth label="Assigned To" value={form.assignedTo} onChange={(e) => setForm({ ...form, assignedTo: e.target.value })} margin="normal" />
          <DateField label="Due Date" value={form.dueDate} onChange={(e) => setForm({ ...form, dueDate: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => createWO.mutate(form)} disabled={!form.title || createWO.isPending}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
