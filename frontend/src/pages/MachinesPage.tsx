import {
  Box,
  Card,
  Typography,
  TextField,
  InputAdornment,
  LinearProgress,
  Button,
} from '@mui/material';
import { Search, Add } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { machinesApi } from '../api/client';
import StatusChip from '../components/StatusChip';
import FilterSelect, { filterValueToParam } from '../components/FilterSelect';
import ResponsiveTable from '../components/ResponsiveTable';
import { ErrorState, EmptyState, TableSkeleton } from '../components/StateViews';
import { parseApiError } from '../utils/validation';
import { useAuth } from '../context/AuthContext';
import type { Machine } from '../types';

export default function MachinesPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const navigate = useNavigate();
  const { hasRole } = useAuth();

  const { data: machines, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['machines', statusFilter, search],
    queryFn: () =>
      machinesApi
        .list({ status: filterValueToParam(statusFilter), search: search || undefined })
        .then((r) => r.data as Machine[]),
    refetchInterval: 10000,
  });

  const columns = [
    {
      key: 'name',
      label: 'Machine',
      render: (m: Machine) => (
        <Box>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>{m.name}</Typography>
          <Typography variant="caption" color="text.secondary">{m.machineId}</Typography>
        </Box>
      ),
    },
    {
      key: 'type',
      label: 'Type',
      hideOnMobile: true,
      render: (m: Machine) => <span style={{ textTransform: 'capitalize' }}>{m.type}</span>,
    },
    {
      key: 'location',
      label: 'Location',
      hideOnMobile: true,
      render: (m: Machine) => m.location,
    },
    {
      key: 'status',
      label: 'Status',
      render: (m: Machine) => <StatusChip status={m.status} />,
    },
    {
      key: 'health',
      label: 'Health',
      render: (m: Machine) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 80 }}>
          <LinearProgress
            variant="determinate"
            value={m.healthScore}
            sx={{
              flex: 1,
              height: 8,
              borderRadius: 4,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                bgcolor: m.healthScore > 70 ? 'success.main' : m.healthScore > 40 ? 'warning.main' : 'error.main',
                borderRadius: 4,
              },
            }}
          />
          <Typography variant="caption">{Math.round(m.healthScore)}</Typography>
        </Box>
      ),
    },
    {
      key: 'risk',
      label: 'Failure Risk',
      render: (m: Machine) => (
        <Typography
          variant="body2"
          sx={{ fontWeight: m.failureProbability > 0.5 ? 700 : 400, color: m.failureProbability > 0.5 ? 'error.main' : 'text.primary' }}
        >
          {Math.round(m.failureProbability * 100)}%
        </Typography>
      ),
    },
    {
      key: 'lastReading',
      label: 'Last Reading',
      hideOnMobile: true,
      render: (m: Machine) => (
        <Typography variant="caption">
          {m.lastReadingAt ? new Date(m.lastReadingAt).toLocaleString() : 'N/A'}
        </Typography>
      ),
    },
  ];

  return (
    <Box sx={{ maxWidth: '100%', overflow: 'hidden' }}>
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'stretch', sm: 'center' }, gap: 2, mb: 3 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }} gutterBottom>
            Machine Fleet
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Monitor equipment health, failure risk, and sensor status
          </Typography>
        </Box>
        {hasRole('admin', 'supervisor') && (
          <Button variant="outlined" startIcon={<Add />} onClick={() => navigate('/admin')} sx={{ alignSelf: { xs: 'stretch', sm: 'auto' } }}>
            Register Machine
          </Button>
        )}
      </Box>

      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2, mb: 3 }}>
        <TextField
          placeholder="Search machines..."
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ flex: 1, maxWidth: { sm: 400 } }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start"><Search /></InputAdornment>
              ),
            },
          }}
        />
        <FilterSelect
          label="Status"
          value={statusFilter}
          onChange={setStatusFilter}
          options={[
            { value: 'all', label: 'All' },
            { value: 'healthy', label: 'Healthy' },
            { value: 'warning', label: 'Warning' },
            { value: 'critical', label: 'Critical' },
            { value: 'offline', label: 'Offline' },
          ]}
        />
      </Box>

      <Card sx={{ overflow: 'hidden' }}>
        {isLoading ? (
          <Box sx={{ p: 2 }}><TableSkeleton rows={5} /></Box>
        ) : isError ? (
          <Box sx={{ p: 2 }}>
            <ErrorState message={parseApiError(error)} onRetry={() => refetch()} />
          </Box>
        ) : !machines?.length ? (
          <EmptyState
            title="No machines found"
            description={search || statusFilter !== 'all' ? 'Try adjusting your filters.' : 'Register a machine to get started.'}
            action={hasRole('admin', 'supervisor') ? (
              <Button variant="contained" onClick={() => navigate('/admin')}>Register Machine</Button>
            ) : undefined}
          />
        ) : (
          <>
            {isFetching && !isLoading && <LinearProgress sx={{ height: 2 }} />}
            <Box sx={{ p: { xs: 1, sm: 0 } }}>
              <ResponsiveTable
                columns={columns}
                rows={machines}
                keyField="machineId"
                onRowClick={(m) => navigate(`/machines/${m.machineId}`)}
              />
            </Box>
          </>
        )}
      </Card>
    </Box>
  );
}
