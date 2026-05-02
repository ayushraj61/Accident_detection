import React, { useState, useEffect } from 'react';
import { useAlerts } from '../context/AlertContext';
import { AlertTriangle, Radio, ShieldCheck, ShieldX, CheckCircle, XCircle, Users, Settings, Clock } from 'lucide-react';

export default function CommandCenter() {
  const { alerts, wsStatus, verifyAlert, dismissAlert, adminSettings, updateAdminSettings } = useAlerts();
  const [viewFilter, setViewFilter] = useState('active'); // 'active', 'verified', 'dismissed'

  const statusColor = wsStatus === 'connected' ? '#10b981' : wsStatus === 'reconnecting' ? '#f59e0b' : '#ef4444';
  const statusLabel = wsStatus === 'connected' ? 'Live — Monitoring' : wsStatus === 'reconnecting' ? 'Reconnecting...' : 'Connecting...';

  const pendingAlerts = alerts.filter(a => a.status === 'pending');
  const verifiedAlerts = alerts.filter(a => a.status === 'verified' || a.status === 'dispatched');
  const dismissedAlerts = alerts.filter(a => a.status === 'dismissed');

  const filteredAlerts = viewFilter === 'active' 
    ? pendingAlerts 
    : viewFilter === 'verified' 
    ? verifiedAlerts 
    : dismissedAlerts;

  // IST Formatter Utility
  const formatToIST = (dateString) => {
    if (!dateString) return '--:--:--';
    let date = new Date(dateString);
    if (isNaN(date.getTime())) {
        const today = new Date().toISOString().split('T')[0];
        date = new Date(`${today}T${dateString}`);
    }
    return new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    }).format(date);
  };

  return (
    <div className="dashboard-container">
      <div className="header" style={{marginBottom: '1rem'}}>
        <div>
          <h1>Central Command Hub</h1>
          <div style={{display: 'flex', alignItems: 'center', gap: '8px', color: statusColor, fontSize: '0.9rem', marginTop: 4}}>
            <span style={{width: 8, height: 8, borderRadius: '50%', background: statusColor, boxShadow: `0 0 8px ${statusColor}`}}></span>
            <span>{statusLabel}</span>
          </div>
        </div>

        {/* Global Fail-Safe Settings */}
        <div className="card" style={{padding: '0.8rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1.5rem', background: 'rgba(255,255,255,0.03)'}}>
           <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem'}}>
             <Settings size={16}/>
             <span>Fail-Safe Window:</span>
           </div>
           <select 
             value={adminSettings.auto_dispatch_window}
             onChange={(e) => updateAdminSettings({ auto_dispatch_window: parseInt(e.target.value) })}
             style={{background: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border)', padding: '4px 8px', borderRadius: 4}}
           >
             <option value={1}>1 Minute</option>
             <option value={2}>2 Minutes</option>
             <option value={5}>5 Minutes</option>
             <option value={10}>10 Minutes</option>
           </select>
        </div>
      </div>

      {/* Stats Bar (Now Interactive Filters) */}
      <div style={{display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap'}}>
        <div className={`card stat-card ${viewFilter === 'active' ? 'active-filter' : ''}`} 
             onClick={() => setViewFilter('active')}
             style={{flex: 1, minWidth: 150, textAlign: 'center', padding: '1rem', cursor: 'pointer', border: viewFilter === 'active' ? '2px solid var(--accent-blue)' : '1px solid var(--border)'}}>
          <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#ef4444'}}>{pendingAlerts.length}</div>
          <div style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>Active Incidents</div>
        </div>
        
        <div className={`card stat-card ${viewFilter === 'verified' ? 'active-filter' : ''}`} 
             onClick={() => setViewFilter('verified')}
             style={{flex: 1, minWidth: 150, textAlign: 'center', padding: '1rem', cursor: 'pointer', border: viewFilter === 'verified' ? '2px solid #10b981' : '1px solid var(--border)'}}>
          <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#10b981'}}>{verifiedAlerts.length}</div>
          <div style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>Verified & Dispatched</div>
        </div>

        <div className={`card stat-card ${viewFilter === 'dismissed' ? 'active-filter' : ''}`} 
             onClick={() => setViewFilter('dismissed')}
             style={{flex: 1, minWidth: 150, textAlign: 'center', padding: '1rem', cursor: 'pointer', border: viewFilter === 'dismissed' ? '2px solid #6b7280' : '1px solid var(--border)'}}>
          <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#6b7280'}}>{dismissedAlerts.length}</div>
          <div style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>False Alarms</div>
        </div>
      </div>

      <div style={{marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <h3 style={{margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px'}}>
          {viewFilter === 'active' ? '🚨 LIVE DISPATCH FEED' : viewFilter === 'verified' ? '✅ COMPLETED DISPATCHES' : '📂 FALSE ALARM ARCHIVE'}
        </h3>
        {viewFilter !== 'active' && (
          <button className="outline" style={{padding: '4px 12px', fontSize: '0.75rem'}} onClick={() => setViewFilter('active')}>
            Back to Live Feed
          </button>
        )}
      </div>

      <div className="grid-2">
        {filteredAlerts.length === 0 ? (
          <div className="card" style={{gridColumn: '1 / -1', textAlign: 'center', padding: '4rem'}}>
            <Radio size={48} style={{color: 'var(--text-muted)', margin: '0 auto 1rem'}} />
            <h3 style={{color: 'var(--text-muted)'}}>No {viewFilter === 'active' ? 'active' : viewFilter} incidents found.</h3>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} verifyAlert={verifyAlert} dismissAlert={dismissAlert} formatToIST={formatToIST} />
          ))
        )}
      </div>
    </div>
  );
}

function AlertCard({ alert, verifyAlert, dismissAlert, formatToIST }) {
  const [severity, setSeverity] = useState(alert.severity);
  const [impact, setImpact] = useState('Significant');
  const [timeLeft, setTimeLeft] = useState('');

  const isVerified = alert.status === 'verified' || alert.status === 'dispatched';
  const isDismissed = alert.status === 'dismissed';
  const borderColor = isVerified ? '#10b981' : isDismissed ? '#6b7280' : '#ef4444';

  useEffect(() => {
    if (alert.status !== 'pending' || !alert.auto_dispatch_at) {
      setTimeLeft('--:--');
      return;
    }
    
    const interval = setInterval(() => {
      const now = new Date().getTime();
      const expiry = new Date(alert.auto_dispatch_at).getTime();
      const diff = expiry - now;
      
      if (diff <= 0) {
        setTimeLeft('DISPATCHING...');
        clearInterval(interval);
      } else {
        const mins = Math.floor(diff / 60000);
        const secs = Math.floor((diff % 60000) / 1000);
        setTimeLeft(`${mins}m ${secs < 10 ? '0' : ''}${secs}s`);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [alert.status, alert.auto_dispatch_at]);

  return (
    <div className={`card alert-card ${isDismissed ? '' : 'critical'}`}
      style={{
        gridColumn: '1 / -1',
        borderColor: borderColor,
        opacity: isDismissed ? 0.5 : 1,
        transition: 'all 0.3s ease',
      }}>
      
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
        <h3 style={{color: 'white', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0}}>
          {isVerified ? <CheckCircle size={20} color="#10b981" /> :
           isDismissed ? <XCircle size={20} color="#6b7280" /> :
           <AlertTriangle size={20} color="#ef4444" />}
          {isVerified ? 'VERIFIED — ' : isDismissed ? 'DISMISSED — ' : 'Pending Verification: '}
          {alert.id.substring(0, 12).toUpperCase()}
        </h3>
        
        <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
          {alert.status === 'pending' && (
            <div style={{display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#f59e0b', fontWeight: 'bold', fontSize: '0.85rem', background: 'rgba(245,158,11,0.1)', padding: '4px 10px', borderRadius: 6}}>
              <Clock size={14}/> AUTO-DISPATCH IN: {timeLeft}
            </div>
          )}
          {alert.eta_minutes && (
            <div style={{color: '#10b981', fontWeight: 'bold', fontSize: '0.85rem'}}>ETA: {alert.eta_minutes} MIN</div>
          )}
          <span style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>{formatToIST(alert.created_at || alert.time)}</span>
        </div>
      </div>

      <div style={{display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1.5rem'}}>
        {/* Left Side: Media */}
        <div>
          {alert.video_clip_url ? (
            <video
              src={`http://localhost:8000${alert.video_clip_url}`}
              poster={alert.thumbnail_b64 ? `data:image/jpeg;base64,${alert.thumbnail_b64}` : undefined}
              controls autoPlay muted loop playsInline
              style={{ width: '100%', maxHeight: '350px', borderRadius: '8px', background: '#000', border: `1px solid ${borderColor}` }}
            />
          ) : alert.thumbnail_b64 ? (
            <img
              src={`data:image/jpeg;base64,${alert.thumbnail_b64}`}
              alt="Crash frame capture"
              style={{ width: '100%', maxHeight: '350px', objectFit: 'contain', borderRadius: '8px', background: '#000', border: `1px solid ${borderColor}` }}
            />
          ) : (
            <div className="video-placeholder"><span>AI Processing...</span></div>
          )}
        </div>

        {/* Right Side: Triage Form */}
        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
          <div className="triage-section">
            <label style={{fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '0.5rem', display: 'block'}}>
              1. Adjust Severity
            </label>
            <div style={{display: 'flex', gap: '0.5rem'}}>
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(s => (
                <button 
                  key={s} 
                  disabled={!alert.status === 'pending'}
                  onClick={() => setSeverity(s)}
                  style={{
                    flex: 1, padding: '6px', fontSize: '0.7rem', borderRadius: 4, cursor: 'pointer',
                    background: severity === s ? (s === 'CRITICAL' ? '#ef4444' : 'var(--accent-blue)') : 'transparent',
                    border: `1px solid ${severity === s ? 'transparent' : 'var(--border)'}`,
                    color: severity === s ? 'white' : 'var(--text-muted)',
                    fontWeight: 600
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="triage-section">
            <label style={{fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '0.5rem', display: 'block'}}>
              2. Scale of Impact (Hospitals)
            </label>
            <div style={{display: 'flex', gap: '0.5rem'}}>
              {[
                {id: 'Minor', label: 'Minor (1-2)'},
                {id: 'Significant', label: 'Sig (3-5)'},
                {id: 'Mass', label: 'Mass (5+)'}
              ].map(i => (
                <button 
                  key={i.id} 
                  disabled={!alert.status === 'pending'}
                  onClick={() => setImpact(i.id)}
                  style={{
                    flex: 1, padding: '10px 6px', fontSize: '0.7rem', borderRadius: 4, cursor: 'pointer',
                    background: impact === i.id ? '#8b5cf6' : 'transparent',
                    border: `1px solid ${impact === i.id ? 'transparent' : 'var(--border)'}`,
                    color: impact === i.id ? 'white' : 'var(--text-muted)',
                    fontWeight: 600
                  }}
                >
                  {i.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{marginTop: 'auto', borderTop: '1px solid var(--border)', paddingTop: '1rem'}}>
             <div style={{fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem'}}>
                <p>📍 Location: {alert.location}</p>
                <p>🏥 Primary Hospital: {alert.hospital_standby}</p>
                {alert.incident_type && <p>🚨 Type: {alert.incident_type}</p>}
                {alert.impact_scale && <p>👥 Scale: {alert.impact_scale}</p>}
             </div>

             {alert.status === 'pending' ? (
                <div style={{display: 'flex', gap: '1rem'}}>
                  <button className="primary" style={{flex: 2}} onClick={() => verifyAlert(alert.id, { severity, impact_scale: impact, incident_type: 'Manual Verification' })}>
                    <ShieldCheck size={16} style={{marginRight: 6}} /> Verify Case
                  </button>
                  <button className="outline" style={{flex: 1}} onClick={() => dismissAlert(alert.id)}>
                    <ShieldX size={16} />
                  </button>
                </div>
             ) : (
                <div style={{
                  textAlign: 'center', padding: '0.75rem', borderRadius: '8px',
                  background: isVerified ? 'rgba(16, 185, 129, 0.1)' : 'rgba(107, 114, 128, 0.1)',
                  color: isVerified ? '#10b981' : '#6b7280',
                  fontWeight: 'bold', fontSize: '0.85rem',
                }}>
                  {isVerified ? '✅ VERIFIED & SENT TO ER' : '❌ DISMISSED (FALSE ALARM)'}
                </div>
             )}
          </div>
        </div>
      </div>
    </div>
  );
}
