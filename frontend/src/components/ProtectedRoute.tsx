import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { PageLoader } from './StateViews';

const ROLE_HIERARCHY: Record<string, string[]> = {
  admin: ['admin', 'supervisor', 'technician', 'operator', 'inspector', 'manager', 'engineer'],
  supervisor: ['supervisor', 'technician', 'operator', 'inspector'],
  technician: ['technician', 'operator'],
  operator: ['operator'],
  inspector: ['inspector'],
  manager: ['manager', 'supervisor'],
  engineer: ['engineer', 'technician'],
};

function hasRole(userRole: string, allowed: string[]): boolean {
  if (userRole === 'admin') return true;
  const permitted = new Set<string>();
  allowed.forEach((r) => (ROLE_HIERARCHY[r] || [r]).forEach((x) => permitted.add(x)));
  return permitted.has(userRole);
}

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: string[];
}

export default function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <PageLoader />;
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />;
  if (roles && user && !hasRole(user.role, roles)) {
    return <Navigate to="/unauthorized" replace />;
  }
  return <>{children}</>;
}
