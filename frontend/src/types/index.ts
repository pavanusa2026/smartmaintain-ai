export interface Machine {
  machineId: string;
  name: string;
  type: string;
  location: string;
  manufacturer: string;
  modelNumber: string;
  installationDate: string;
  status: 'healthy' | 'warning' | 'critical' | 'offline';
  lastReadingAt?: string;
  healthScore: number;
  failureProbability: number;
  lastMaintenanceDate?: string;
  operatingHours: number;
  productionLine: string;
}

export interface SensorReading {
  readingId: string;
  machineId: string;
  timestamp: string;
  temperature: number;
  vibration: number;
  pressure: number;
  powerConsumption: number;
  rotationalSpeed: number;
  operatingLoad: number;
  anomalyScore: number;
}

export interface Alert {
  alertId: string;
  machineId: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  alertType: string;
  title: string;
  explanation: string;
  recommendedAction: string;
  confidence: number;
  status: 'new' | 'acknowledged' | 'investigating' | 'closed';
  createdAt: string;
  acknowledgedBy?: string;
  investigationNotes?: string;
  assignedTo?: string;
}

export interface WorkOrder {
  workOrderId: string;
  machineId: string;
  alertId?: string;
  title: string;
  description: string;
  priority: 'low' | 'normal' | 'high' | 'emergency';
  assignedTo?: string;
  dueDate?: string;
  status: 'open' | 'in_progress' | 'completed' | 'canceled';
  resolutionNotes?: string;
  actualFailureFound?: boolean;
  createdAt: string;
  completedAt?: string;
}

export interface Inspection {
  inspectionId: string;
  productId: string;
  imageUrl: string;
  predictedResult: string;
  defectType: string;
  confidence: number;
  reviewedResult?: string;
  reviewedBy?: string;
  createdAt: string;
}

export interface FailurePrediction {
  machineId: string;
  failureProbability: number;
  predictionWindowDays: number;
  likelyFailureType: string;
  confidence: number;
  healthScore: number;
  anomalyScore: number;
  remainingUsefulLifeHours: number;
  modelVersion: string;
  primaryConcern: string;
  recommendedAction: string;
}

export interface DashboardStats {
  totalMachines: number;
  healthyMachines: number;
  warningMachines: number;
  criticalMachines: number;
  offlineMachines: number;
  openWorkOrders: number;
  defectsDetectedToday: number;
  activeAlerts: number;
  estimatedDowntimeAvoidedHours: number;
}

export interface AssistantResponse {
  answer: string;
  sources: { title: string; section: string; revisionDate: string }[];
  safetyNotice: string;
  humanReviewReminder: string;
}

export interface ReportsSummary {
  totalAlerts: number;
  closedAlerts: number;
  alertResponseRate: number;
  totalWorkOrders: number;
  completedWorkOrders: number;
  maintenanceCompletionRate: number;
  totalInspections: number;
  defectRate: number;
  averageFailureRisk: number;
  machineAvailability: number;
}

export interface User {
  email: string;
  name: string;
  role: string;
}
