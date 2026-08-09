import { Chip } from '@mui/material';

const statusColors: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
  healthy: 'success',
  warning: 'warning',
  critical: 'error',
  offline: 'default',
  new: 'error',
  acknowledged: 'warning',
  investigating: 'warning',
  closed: 'default',
  open: 'error',
  in_progress: 'warning',
  completed: 'success',
  canceled: 'default',
  low: 'default',
  medium: 'warning',
  high: 'error',
  critical_severity: 'error',
  pass: 'success',
  fail: 'error',
};

interface StatusChipProps {
  status: string;
  size?: 'small' | 'medium';
}

export default function StatusChip({ status, size = 'small' }: StatusChipProps) {
  const color = statusColors[status] || 'default';
  return (
    <Chip
      label={status.replace(/_/g, ' ')}
      color={color}
      size={size}
      variant="filled"
      sx={{ textTransform: 'capitalize', fontWeight: 600 }}
    />
  );
}
