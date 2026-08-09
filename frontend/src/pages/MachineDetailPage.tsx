import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Divider,
  Chip,
  Alert as MuiAlert,
} from '@mui/material';
import { ArrowBack, Refresh } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { machinesApi, alertsApi } from '../api/client';
import StatusChip from '../components/StatusChip';
import { ErrorState, EmptyState, ChartSkeleton } from '../components/StateViews';
import { parseApiError } from '../utils/validation';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export default function MachineDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const machineQuery = useQuery({
    queryKey: ['machine', id],
    queryFn: () => machinesApi.get(id!).then((r) => r.data),
    enabled: !!id,
    retry: 1,
  });

  const readingsQuery = useQuery({
    queryKey: ['readings', id],
    queryFn: () => machinesApi.getReadings(id!, 60).then((r) => r.data),
    enabled: !!id && !!machineQuery.data,
    refetchInterval: 10000,
  });

  const predictionQuery = useQuery({
    queryKey: ['prediction', id],
    queryFn: () => machinesApi.getPrediction(id!).then((r) => r.data),
    enabled: !!id && !!machineQuery.data,
    refetchInterval: 15000,
  });

  const alertsQuery = useQuery({
    queryKey: ['alerts', 'machine', id],
    queryFn: () => alertsApi.list({ machineId: id }).then((r) => r.data),
    enabled: !!id,
  });

  const runPrediction = useMutation({
    mutationFn: () => machinesApi.getPrediction(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prediction', id] });
      queryClient.invalidateQueries({ queryKey: ['machine', id] });
    },
  });

  if (machineQuery.isLoading) {
    return <Box sx={{ p: 2 }}><ChartSkeleton height={400} /></Box>;
  }

  if (machineQuery.isError) {
    const is404 = (machineQuery.error as { response?: { status?: number } })?.response?.status === 404;
    return (
      <Box>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/machines')} sx={{ mb: 2 }}>Back</Button>
        <ErrorState
          message={is404 ? 'Machine not found. It may have been removed.' : parseApiError(machineQuery.error)}
          onRetry={is404 ? undefined : () => machineQuery.refetch()}
        />
      </Box>
    );
  }

  const machine = machineQuery.data;
  if (!machine) return null;

  const readings = readingsQuery.data || [];
  const prediction = predictionQuery.data;
  const activeAlerts = (alertsQuery.data || []).filter(
    (a: { status: string }) => !['closed'].includes(a.status)
  );

  const chartData = readings.map(
    (r: { timestamp: string; temperature: number; vibration: number; powerConsumption: number; anomalyScore: number }) => ({
      time: new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      temperature: r.temperature,
      vibration: r.vibration,
      power: r.powerConsumption,
      anomaly: (r.anomalyScore || 0) * 100,
    })
  );

  return (
    <Box sx={{ maxWidth: '100%', overflow: 'hidden' }}>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/machines')} sx={{ mb: 2 }}>
        Back to Machines
      </Button>

      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { xs: 'flex-start', sm: 'center' }, justifyContent: 'space-between', gap: 2, mb: 3 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>{machine.name}</Typography>
          <Typography variant="body2" color="text.secondary">
            {machine.machineId} · {machine.location} · {machine.productionLine || 'N/A'}
          </Typography>
        </Box>
        <StatusChip status={machine.status} size="medium" />
      </Box>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Sensor Trends</Typography>
              {readingsQuery.isLoading ? (
                <ChartSkeleton height={280} />
              ) : readingsQuery.isError ? (
                <ErrorState message={parseApiError(readingsQuery.error)} onRetry={() => readingsQuery.refetch()} />
              ) : chartData.length === 0 ? (
                <EmptyState title="No sensor readings yet" description="Readings will appear when the simulator or sensors send data." />
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Line type="monotone" dataKey="temperature" stroke="#f57c00" name="Temp (°C)" dot={false} strokeWidth={2} />
                    <Line type="monotone" dataKey="vibration" stroke="#1565c0" name="Vibration" dot={false} strokeWidth={2} />
                    <Line type="monotone" dataKey="power" stroke="#2e7d32" name="Power (kW)" dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Latest Sensor Values</Typography>
              {readings.length > 0 ? (
                <Grid container spacing={2}>
                  {[
                    ['Temperature', `${readings[readings.length - 1].temperature}°C`],
                    ['Vibration', readings[readings.length - 1].vibration],
                    ['Pressure', `${readings[readings.length - 1].pressure} psi`],
                    ['Power', `${readings[readings.length - 1].powerConsumption} kW`],
                    ['Speed', `${readings[readings.length - 1].rotationalSpeed} RPM`],
                    ['Load', `${readings[readings.length - 1].operatingLoad}%`],
                  ].map(([label, value]) => (
                    <Grid size={{ xs: 6, sm: 4 }} key={label as string}>
                      <Typography variant="caption" color="text.secondary">{label}</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>{value}</Typography>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Typography color="text.secondary" variant="body2">No readings available</Typography>
              )}
            </CardContent>
          </Card>

          {activeAlerts.length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Active Alerts ({activeAlerts.length})</Typography>
                {activeAlerts.map((alert: { alertId: string; title: string; severity: string; explanation: string }) => (
                  <MuiAlert key={alert.alertId} severity={alert.severity === 'critical' ? 'error' : alert.severity === 'high' ? 'warning' : 'info'} sx={{ mb: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{alert.title}</Typography>
                    <Typography variant="caption">{alert.explanation}</Typography>
                  </MuiAlert>
                ))}
              </CardContent>
            </Card>
          )}
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Equipment Profile</Typography>
              {[
                ['Type', machine.type],
                ['Manufacturer', machine.manufacturer],
                ['Model', machine.modelNumber],
                ['Installed', machine.installationDate],
                ['Operating Hours', `${machine.operatingHours?.toLocaleString()}h`],
                ['Last Maintenance', machine.lastMaintenanceDate || 'N/A'],
                ['Production Line', machine.productionLine],
              ].map(([label, value]) => (
                <Box key={label as string} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.75, gap: 1 }}>
                  <Typography variant="body2" color="text.secondary">{label}</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, textTransform: 'capitalize', textAlign: 'right' }}>{value}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">AI Prediction</Typography>
                <Button size="small" startIcon={<Refresh />} onClick={() => runPrediction.mutate()} disabled={runPrediction.isPending || predictionQuery.isFetching}>
                  Refresh
                </Button>
              </Box>

              {predictionQuery.isLoading ? (
                <ChartSkeleton height={200} />
              ) : predictionQuery.isError ? (
                <ErrorState message={parseApiError(predictionQuery.error)} onRetry={() => predictionQuery.refetch()} />
              ) : prediction ? (
                <>
                  <Box sx={{ textAlign: 'center', mb: 2 }}>
                    <Typography variant="h3" sx={{ fontWeight: 700, color: 'primary.main' }}>{Math.round(prediction.healthScore)}</Typography>
                    <Typography variant="caption" color="text.secondary">Health Score / 100</Typography>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    {[
                      ['Failure Risk (7d)', `${Math.round(prediction.failureProbability * 100)}%`, prediction.failureProbability > 0.5],
                      ['Anomaly Score', `${Math.round(prediction.anomalyScore * 100)}%`, false],
                      ['Remaining Life', `~${Math.round(prediction.remainingUsefulLifeHours)}h`, false],
                      ['Model', prediction.modelVersion, false],
                    ].map(([label, value, warn]) => (
                      <Box key={label as string} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">{label}</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: warn ? 'error.main' : 'text.primary' }}>{value}</Typography>
                      </Box>
                    ))}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2">Likely Failure</Typography>
                      <Chip label={String(prediction.likelyFailureType).replace(/_/g, ' ')} size="small" sx={{ textTransform: 'capitalize' }} />
                    </Box>
                  </Box>
                  <MuiAlert severity={prediction.failureProbability > 0.7 ? 'error' : prediction.failureProbability > 0.4 ? 'warning' : 'info'} sx={{ mt: 2 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{prediction.primaryConcern}</Typography>
                    <Typography variant="caption">{prediction.recommendedAction}</Typography>
                  </MuiAlert>
                </>
              ) : null}
              {runPrediction.isError && (
                <MuiAlert severity="error" sx={{ mt: 1 }}>{parseApiError(runPrediction.error)}</MuiAlert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
