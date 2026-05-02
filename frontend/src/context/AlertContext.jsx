import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react';

const AlertContext = createContext(null);

export function useAlerts() {
  return useContext(AlertContext);
}

export function AlertProvider({ children }) {
  const [alerts, setAlerts] = useState([]);
  const [ambulanceLocations, setAmbulanceLocations] = useState({});
  const [wsStatus, setWsStatus] = useState('connecting');
  const [adminSettings, setAdminSettings] = useState({ auto_dispatch_window: 2 });
  const [fleetVersion, setFleetVersion] = useState(0); // Used to trigger fleet re-fetches
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const audioRef = useRef(new Audio('https://assets.mixkit.co/active_storage/sfx/2568/2568-preview.mp3'));

  const fetchInitial = useCallback(async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/emergency/incidents');
        const data = await res.json();
        const formatted = data.map(alert => {
          const lat = alert.lat || 0;
          const lng = alert.lng || 0;
          return {
            id: alert.id,
            time: new Date(alert.created_at || Date.now()).toLocaleTimeString(),
            timestamp: new Date(alert.created_at || Date.now()).getTime(),
            location: `${lat.toFixed(4)}° N, ${Math.abs(lng).toFixed(4)}° W`,
            locationRaw: { lat, lng },
            severity: (alert.severity || 'HIGH').toUpperCase(),
            confidence: alert.confidence || 0,
            video_clip_url: alert.video_clip_url || null,
            thumbnail_b64: alert.thumbnail_b64 || null,
            hospital_id: alert.hospital_id,
            dispatched_ambulances: [],
            dispatched_ambulance_names: alert.assigned_fleet ? alert.assigned_fleet.split(',') : [],
            matched_hospitals: [],
            hospital_standby: 'Hospital Notified',
            status: alert.status || 'pending',
            ambulanceStatus: alert.assigned_fleet ? 'dispatched' : 'idle',
            hospitalStatus: alert.hospital_status || 'notified',
            impact_scale: alert.impact_scale,
            incident_type: alert.incident_type
          };
        });
        setAlerts(formatted.filter(a => a.status !== 'resolved'));
      } catch (err) {
        console.error("Failed to fetch initial incidents", err);
      }
  }, []);

  useEffect(() => {
    fetchInitial();

    function connectWebSocket() {
      if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) return;
      const ws = new WebSocket('ws://localhost:8000/api/v1/emergency/ws');
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus('connected');
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === 'NEW_ACCIDENT') {
            const alert = payload.alert;
            const newAlert = {
              id: alert.id,
              time: new Date().toLocaleTimeString(),
              timestamp: Date.now(),
              location: `${(alert.lat || 0).toFixed(4)}° N, ${Math.abs(alert.lng || 0).toFixed(4)}° W`,
              locationRaw: { lat: alert.lat, lng: alert.lng },
              severity: (alert.severity || 'HIGH').toUpperCase(),
              confidence: alert.confidence || 0,
              video_clip_url: alert.video_clip_url || null,
              thumbnail_b64: alert.thumbnail_b64 || null,
              hospital_id: alert.hospital_id,
              status: 'pending',
              ambulanceStatus: 'idle',
              hospitalStatus: 'notified',
              dispatched_ambulance_names: [],
              impact_scale: alert.impact_scale,
              incident_type: alert.incident_type
            };
            audioRef.current.play().catch(() => {});
            setAlerts(prev => [newAlert, ...prev]);
          } else if (payload.event === 'DISPATCH_VERIFIED') {
            setAlerts(prev => prev.map(a => 
              a.id === payload.alert_id 
                ? { 
                    ...a, 
                    status: 'verified', 
                    severity: (payload.alert?.severity || a.severity).toUpperCase(),
                    impact_scale: payload.alert?.impact_scale || a.impact_scale,
                    hospital_id: payload.alert?.hospital_id || a.hospital_id
                  } 
                : a
            ));
          } else if (payload.event === 'AMBULANCE_ASSIGNED') {
            setAlerts(prev => prev.map(a => 
              a.id === payload.alert_id 
                ? { 
                    ...a, 
                    status: 'dispatched', 
                    ambulanceStatus: 'dispatched', 
                    hospitalStatus: 'inbound', 
                    dispatched_ambulance_names: payload.ambulance_names 
                  } 
                : a
            ));
            setFleetVersion(v => v + 1);
          } else if (payload.event === 'AMBULANCE_STATUS_UPDATED') {
            setAlerts(prev => prev.map(a => a.id === payload.alert_id ? { ...a, ambulanceStatus: payload.status } : a));
          } else if (payload.event === 'HOSPITAL_STATUS_UPDATED') {
            setAlerts(prev => prev.map(a => a.id === payload.alert_id ? { ...a, hospitalStatus: payload.status } : a));
            if (payload.status === 'admitted') setFleetVersion(v => v + 1);
          } else if (payload.event === 'CASE_RESOLVED') {
            setAlerts(prev => prev.filter(a => a.id !== payload.alert_id));
            setFleetVersion(v => v + 1);
          } else if (payload.event === 'FLEET_RELEASED') {
            setFleetVersion(v => v + 1);
          } else if (payload.event === 'FALSE_ALARM') {
            setAlerts(prev => prev.map(a => a.id === payload.alert_id ? { ...a, status: 'dismissed' } : a));
          } else if (payload.event === 'LOCATION_UPDATE') {
            setAmbulanceLocations(prev => ({
              ...prev,
              [payload.ambulance_id]: { lat: payload.lat, lng: payload.lng }
            }));
          }
        } catch (err) {
          console.error('[AlertProvider] Message error:', err);
        }
      };

      ws.onclose = () => {
        setWsStatus('reconnecting');
        reconnectTimerRef.current = setTimeout(connectWebSocket, 3000);
      };
    }

    connectWebSocket();
    return () => {
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [fetchInitial]);

  const verifyAlert = useCallback((alertId, triageData = {}) => {
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'verified', ...triageData } : a));
    fetch('http://localhost:8000/api/v1/emergency/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_id: alertId, action: 'verify_dispatch', ...triageData }),
    }).catch(() => {});
  }, []);

  const dismissAlert = useCallback((alertId) => {
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'dismissed' } : a));
    fetch('http://localhost:8000/api/v1/emergency/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_id: alertId, action: 'dismiss' }),
    }).catch(() => {});
  }, []);

  const updateHospitalStatus = useCallback((alertId, newStatus) => {
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, hospitalStatus: newStatus } : a));
    if (newStatus === 'admitted') setFleetVersion(v => v + 1);
    
    fetch('http://localhost:8000/api/v1/emergency/hospital/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_id: alertId, status: newStatus }),
    }).catch(() => {});
  }, []);

  const dischargePatient = useCallback((alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
    fetch('http://localhost:8000/api/v1/emergency/hospital/discharge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_id: alertId }),
    }).catch(() => {});
  }, []);

  const updateAmbulanceStatus = useCallback((alertId, newStatus) => {
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, ambulanceStatus: newStatus } : a));
    fetch('http://localhost:8000/api/v1/emergency/ambulance/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_id: alertId, status: newStatus }),
    }).catch(() => {});
  }, []);

  const assignAmbulances = useCallback((alertId, ambulanceIds) => {
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'dispatched', ambulanceStatus: 'dispatched', hospitalStatus: 'inbound' } : a));
    fetch('http://localhost:8000/api/v1/emergency/assign-ambulances', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_id: alertId, ambulance_ids: ambulanceIds }),
    }).catch(() => {});
  }, []);

  const value = {
    alerts,
    ambulanceLocations,
    wsStatus,
    adminSettings,
    fleetVersion,
    verifyAlert,
    dismissAlert,
    updateHospitalStatus,
    updateAmbulanceStatus,
    dischargePatient,
    assignAmbulances,
  };

  return <AlertContext.Provider value={value}>{children}</AlertContext.Provider>;
}
