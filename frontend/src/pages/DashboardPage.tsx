import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  PrecisionManufacturing,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Assignment,
  NotificationsActive,
  TrendingUp,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi, machinesApi, alertsApi } from '../api/client';
import StatusChip from '../components/StatusChip';
import { parseApiError } from '../utils/validation';
import { useNavigate } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const COLORS = ['#2e7d32', '#f57c00', '#c62828', '#9e9e9e'];

function StatCard({
  title,
  value,
  icon,
  color,
  subtitle,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={700} sx={{ color }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              bgcolor: `${color}15`,
              borderRadius: 2,
              p: 1.5,
              display: 'flex',
              color,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.getStats().then((r) => r.data),
    refetchInterval: 10000,
  });

  const { data: machines } = useQuery({
    queryKey: ['machines'],
    queryFn: () => machinesApi.list().then((r) => r.data),
    refetchInterval: 10000,
  });

  const { data: alerts } = useQuery({
    queryKey: ['alerts-active'],
    queryFn: () => alertsApi.list().then((r) => r.data),
    refetchInterval: 10000,
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{parseApiError(error)}</Alert>;
  }

  const pieData = [
    { name: 'Healthy', value: stats?.healthyMachines || 0 },
    { name: 'Warning', value: stats?.warningMachines || 0 },
    { name: 'Critical', value: stats?.criticalMachines || 0 },
    { name: 'Offline', value: stats?.offlineMachines || 0 },
  ];

  const lineData = (machines || []).map((m: { name: string; healthScore: number; failureProbability: number }) => ({
    name: m.name.split(' ').slice(-1)[0],
    health: m.healthScore,
    risk: Math.round(m.failureProbability * 100),
  }));

  const recentAlerts = (alerts || []).slice(0, 5);

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Executive Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Real-time overview of equipment health and maintenance operations
      </Typography>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Total Machines"
            value={stats?.totalMachines || 0}
            icon={<PrecisionManufacturing />}
            color="#1565c0"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Healthy"
            value={stats?.healthyMachines || 0}
            icon={<CheckCircle />}
            color="#2e7d32"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Warnings"
            value={stats?.warningMachines || 0}
            icon={<Warning />}
            color="#f57c00"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Critical"
            value={stats?.criticalMachines || 0}
            icon={<ErrorIcon />}
            color="#c62828"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Active Alerts"
            value={stats?.activeAlerts || 0}
            icon={<NotificationsActive />}
            color="#e65100"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Open Work Orders"
            value={stats?.openWorkOrders || 0}
            icon={<Assignment />}
            color="#6a1b9a"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Defects Today"
            value={stats?.defectsDetectedToday || 0}
            icon={<ErrorIcon />}
            color="#ad1457"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Downtime Avoided"
            value={`${stats?.estimatedDowntimeAvoidedHours || 0}h`}
            icon={<TrendingUp />}
            color="#00838f"
            subtitle="Estimated this period"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Machine Health Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 7 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Health Score vs Failure Risk
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={lineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="health" fill="#1565c0" name="Health Score" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="risk" fill="#c62828" name="Failure Risk %" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Alerts
              </Typography>
              {recentAlerts.length === 0 ? (
                <Typography color="text.secondary">No active alerts</Typography>
              ) : (
                recentAlerts.map((alert: { alertId: string; title: string; severity: string; machineId: string; status: string }) => (
                  <Box
                    key={alert.alertId}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      py: 1.5,
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'action.hover' },
                    }}
                    onClick={() => navigate('/alerts')}
                  >
                    <Box>
                      <Typography variant="body2" fontWeight={600}>
                        {alert.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {alert.machineId}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <StatusChip status={alert.severity} />
                      <StatusChip status={alert.status} />
                    </Box>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
