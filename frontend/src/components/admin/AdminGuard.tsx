import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { apiClient } from '../../api/client';

interface AdminGuardProps {
  children: React.ReactNode;
}

const AdminGuard: React.FC<AdminGuardProps> = ({ children }) => {
  const location = useLocation();
  const isAuthenticated = apiClient.isAuthenticated();

  useEffect(() => {
    // Verify token is still valid on mount
    if (isAuthenticated) {
      apiClient.getAdminStats().catch(() => {
        // Token is invalid, clear it
        apiClient.clearAuthToken();
        window.location.reload();
      });
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    // Redirect to login with the intended destination
    return <Navigate to="/admin" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export default AdminGuard;