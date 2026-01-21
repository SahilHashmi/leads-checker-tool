import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import DeviceKeyPage from './pages/DeviceKeyPage';
import UploadPage from './pages/UploadPage';
import AdminLogin from './pages/AdminLogin';
import AdminKeys from './pages/AdminKeys';
import AdminLeads from './pages/AdminLeads';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);

  useEffect(() => {
    const deviceKey = localStorage.getItem('deviceKey');
    const isValid = localStorage.getItem('deviceKeyValid') === 'true';
    setIsAuthenticated(!!deviceKey && isValid);

    const adminToken = localStorage.getItem('adminToken');
    setIsAdminAuthenticated(!!adminToken);
  }, []);

  const handleDeviceKeySuccess = () => {
    setIsAuthenticated(true);
  };

  const handleAdminLoginSuccess = () => {
    setIsAdminAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('deviceKey');
    localStorage.removeItem('deviceKeyValid');
    setIsAuthenticated(false);
  };

  const handleAdminLogout = () => {
    localStorage.removeItem('adminToken');
    setIsAdminAuthenticated(false);
  };

  return (
    <BrowserRouter>
      <Routes>
        {/* User Tool Routes */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <UploadPage onLogout={handleLogout} />
            ) : (
              <DeviceKeyPage onSuccess={handleDeviceKeySuccess} />
            )
          }
        />

        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            isAdminAuthenticated ? (
              <Navigate to="/admin/keys" replace />
            ) : (
              <AdminLogin onSuccess={handleAdminLoginSuccess} />
            )
          }
        />
        <Route
          path="/admin/keys"
          element={
            isAdminAuthenticated ? (
              <AdminKeys onLogout={handleAdminLogout} />
            ) : (
              <Navigate to="/admin" replace />
            )
          }
        />
        <Route
          path="/admin/leads"
          element={
            isAdminAuthenticated ? (
              <AdminLeads onLogout={handleAdminLogout} />
            ) : (
              <Navigate to="/admin" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
