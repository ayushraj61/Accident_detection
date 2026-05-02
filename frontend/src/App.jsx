import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { AlertProvider } from './context/AlertContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import CommandCenter from './pages/CommandCenter';
import HospitalDashboard from './pages/HospitalDashboard';
import AmbulanceDashboard from './pages/AmbulanceDashboard';
import CameraFeed from './pages/CameraFeed';
import Login from './pages/Login';
import RegisterHospital from './pages/RegisterHospital';
import { Activity, ShieldAlert, Truck, Camera, LogOut, User } from 'lucide-react';
import './index.css';

function ProtectedRoute({ children, allowedRole }) {
  const { isAuthenticated, role, loading } = useAuth();
  
  if (loading) return <div className="dashboard-container">Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" />;
  
  if (allowedRole && role !== allowedRole) {
    // If user is logged in but unauthorized for this specific page,
    // redirect them to their appropriate dashboard
    if (role === 'hospital') return <Navigate to="/hospital" />;
    if (role === 'ambulance') return <Navigate to="/ambulance" />;
    if (role === 'admin') return <Navigate to="/" />;
  }
  
  return children;
}

function NavBar() {
  const location = useLocation();
  const { isAuthenticated, logout, role, user } = useAuth();
  
  const links = [
    { to: '/', icon: <ShieldAlert size={16}/>, label: 'Command Center', color: '#3b82f6', role: 'admin' },
    { to: '/hospital', icon: <Activity size={16}/>, label: 'ER Dashboard', color: '#10b981', role: 'hospital' },
    { to: '/ambulance', icon: <Truck size={16}/>, label: 'Driver View', color: '#f59e0b', role: 'ambulance' },
    { to: '/camera', icon: <Camera size={16}/>, label: 'CCTV Sandbox', color: '#a855f7', role: 'admin' },
  ];

  return (
    <div className="nav-panel" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
      <div style={{display: 'flex', gap: '2rem'}}>
        {links.map(link => {
          // Public links always show
          if (link.public) {
            const isActive = location.pathname === link.to;
            return <NavLink key={link.to} link={link} isActive={isActive} />;
          }
          // Authenticated role-specific links
          if (isAuthenticated && role === link.role) {
            const isActive = location.pathname === link.to;
            return <NavLink key={link.to} link={link} isActive={isActive} />;
          }
          return null;
        })}
      </div>

      <div style={{display: 'flex', alignItems: 'center', gap: '1.5rem'}}>
        {isAuthenticated ? (
          <>
            <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)'}}>
              <User size={14}/>
              <span>{user?.name || user?.unit_name || 'Admin'}</span>
              <span style={{fontSize: '0.7rem', padding: '2px 6px', background: 'rgba(255,255,255,0.1)', borderRadius: 10, textTransform: 'uppercase'}}>
                {role}
              </span>
            </div>
            <button onClick={logout} style={{
              background: 'transparent', border: 'none', color: 'var(--accent-red)', 
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem',
              fontSize: '0.85rem', fontWeight: 600, padding: 0
            }}>
              <LogOut size={14}/> Logout
            </button>
          </>
        ) : (
          location.pathname !== '/login' && (
            <Link to="/login" style={{color: 'var(--accent-blue)', textDecoration: 'none', fontWeight: 600, fontSize: '0.9rem'}}>
              Member Login
            </Link>
          )
        )}
      </div>
    </div>
  );
}

function NavLink({ link, isActive }) {
  return (
    <Link to={link.to} style={{
      display: 'flex', alignItems: 'center', gap: '0.5rem',
      color: isActive ? link.color : 'var(--text-muted)',
      borderBottom: isActive ? `2px solid ${link.color}` : '2px solid transparent',
      paddingBottom: '0.5rem',
      transition: 'all 0.2s ease',
      textDecoration: 'none',
      fontWeight: 600,
      fontSize: '0.9rem'
    }}>
      {link.icon} {link.label}
    </Link>
  );
}

function App() {
  return (
    <AuthProvider>
      <AlertProvider>
        <Router>
          <NavBar />
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<RegisterHospital />} />
            <Route path="/camera" element={
              <ProtectedRoute allowedRole="admin">
                <CameraFeed />
              </ProtectedRoute>
            } />

            {/* Role-Based Redirects for root */}
            <Route path="/" element={
              <ProtectedRoute allowedRole="admin">
                <CommandCenter />
              </ProtectedRoute>
            } />

            {/* Protected Hospital Routes */}
            <Route path="/hospital" element={
              <ProtectedRoute allowedRole="hospital">
                <HospitalDashboard />
              </ProtectedRoute>
            } />

            {/* Protected Ambulance Routes */}
            <Route path="/ambulance" element={
              <ProtectedRoute allowedRole="ambulance">
                <AmbulanceDashboard />
              </ProtectedRoute>
            } />
          </Routes>
        </Router>
      </AlertProvider>
    </AuthProvider>
  );
}

export default App;
