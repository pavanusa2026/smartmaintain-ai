import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  LinearProgress,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '../api/client';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

function MetricCard({ title, value, unit = '%', color = '#1565c0' }: { title: string; value: number; unit?: string; color?: string }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>{title}</Typography>
        <Typography variant="h4" fontWeight={700} sx={{ color }}>{value}{unit}</Typography>
        <LinearProgress
          variant="determinate"
          value={Math.min(value, 100)}
          sx={{ mt: 1, height: 6, borderRadius: 3, bgcolor: 'grey.200', '& .MuiLinearProgress-bar': { bgcolor: color, borderRadius: 3 } }}
        />
      </CardContent>
    </Card>
  );
}

export default function ReportsPage() {
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['reports-summary'],
    queryFn: () => reportsApi.getSummary().then((r) => r.data),
  });

  if (isLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">Failed to load reports</Alert>;

  const chartData = [
    { name: 'Alert Response', value: summary.alertResponseRate },
    { name: 'Maintenance Completion', value: summary.maintenanceCompletionRate },
    { name: 'Machine Availability', value: summary.machineAvailability },
    { name: 'Defect Rate', value: summary.defectRate },
  ];

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>Reports & Analytics</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Operational metrics and AI performance indicators
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard title="Alert Response Rate" value={summary.alertResponseRate} color="#1565c0" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard title="Maintenance Completion" value={summary.maintenanceCompletionRate} color="#2e7d32" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard title="Machine Availability" value={summary.machineAvailability} color="#00838f" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard title="Average Failure Risk" value={summary.averageFailureRisk} color="#c62828" />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Performance Metrics</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(v: number) => `${v}%`} />
                  <Bar dataKey="value" fill="#1565c0" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Summary Statistics</Typography>
              {[
                ['Total Alerts', summary.totalAlerts],
                ['Closed Alerts', summary.closedAlerts],
                ['Total Work Orders', summary.totalWorkOrders],
                ['Completed Work Orders', summary.completedWorkOrders],
                ['Total Inspections', summary.totalInspections],
                ['Defect Rate', `${summary.defectRate}%`],
              ].map(([label, value]) => (
                <Box key={label as string} sx={{ display: 'flex', justifyContent: 'space-between', py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="body2" color="text.secondary">{label}</Typography>
                  <Typography variant="body2" fontWeight={600}>{value}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
