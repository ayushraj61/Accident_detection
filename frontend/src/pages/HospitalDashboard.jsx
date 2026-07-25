import React, { useState, useEffect, useRef } from 'react';
import { useAlerts } from '../context/AlertContext';
import { useAuth } from '../context/AuthContext';
import { Activity, Bed, AlertTriangle, Truck, Plus, MapPin, CheckCircle, Clock, ChevronDown, UserMinus } from 'lucide-react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const ambulanceIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/1048/1048329.png',
    iconSize: [32, 32],
});

export default function HospitalDashboard() {
  const { alerts, updateHospitalStatus, assignAmbulances, dischargePatient, ambulanceLocations, fleetVersion } = useAlerts();
  const { user } = useAuth();
  const [ambulances, setAmbulances] = useState([]);
  const [viewFilter, setViewFilter] = useState('new'); 
  const [showAddAmb, setShowAddAmb] = useState(false);
  const [openDropdown, setOpenDropdown] = useState(null); // Case ID
  const [selectedAmbs, setSelectedAmbs] = useState({}); // {caseId: [ids]}

  useEffect(() => {
    fetchAmbulances();
  }, [fleetVersion]);

  const fetchAmbulances = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/hospital/ambulances');
      setAmbulances(res.data);
    } catch (err) { console.error(err); }
  };

  // Logic for filtering alerts
  // Logic for filtering alerts: Show alerts assigned to ME or alerts that are UNCLAIMED (null)
  const myAlerts = alerts.filter(a => (a.hospital_id === user?.id || !a.hospital_id) && a.status !== 'resolved');
  
  const newAlerts = myAlerts.filter(a => (a.hospitalStatus === 'notified' || a.status === 'verified') && a.status !== 'dispatched' && (a.dispatched_ambulance_names || []).length === 0);
  const ongoingAlerts = myAlerts.filter(a => (a.status === 'dispatched' || a.hospitalStatus === 'inbound' || (a.dispatched_ambulance_names || []).length > 0) && a.hospitalStatus !== 'admitted');
  const admittedAlerts = myAlerts.filter(a => a.hospitalStatus === 'admitted');

  const filteredAlerts = viewFilter === 'new' ? newAlerts : viewFilter === 'ongoing' ? ongoingAlerts : admittedAlerts;

  const toggleAmbulance = (caseId, ambId) => {
    const current = selectedAmbs[caseId] || [];
    const updated = current.includes(ambId) ? current.filter(id => id !== ambId) : [...current, ambId];
    setSelectedAmbs({...selectedAmbs, [caseId]: updated});
  };

  // IST Formatter Utility
  const formatToIST = (dateString) => {
    if (!dateString) return '--:--:--';
    // If it's already a formatted time string (has am/pm), just return it
    if (typeof dateString === 'string' && (dateString.toLowerCase().includes('am') || dateString.toLowerCase().includes('pm'))) {
      return dateString;
    }
    
    let date = new Date(dateString);
    if (isNaN(date.getTime())) {
        const today = new Date().toISOString().split('T')[0];
        date = new Date(`${today}T${dateString}`);
    }
    
    if (isNaN(date.getTime())) return dateString; // Last resort fallback

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
      <div className="header">
        <h1>{user?.name}</h1>
        <div style={{display: 'flex', alignItems: 'center', gap: '8px', color: '#10b981'}}>
          <span style={{width: 8, height: 8, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981'}}></span>
          <span>Receiving Mode Ready</span>
        </div>
      </div>

      <div style={{display: 'grid', gridTemplateColumns: '1fr 350px', gap: '2rem'}}>
        <div>
          {/* STATS TABS */}
          <div style={{display: 'flex', gap: '1rem', marginBottom: '1.5rem'}}>
            <div className={`card stat-card ${viewFilter === 'new' ? 'active-filter' : ''}`} 
              onClick={() => setViewFilter('new')}
              style={{flex: 1, cursor: 'pointer', borderTop: viewFilter === 'new' ? '4px solid var(--accent-red)' : '4px solid transparent'}}>
              <AlertTriangle size={24} color="var(--accent-red)"/>
              <div style={{fontSize: '1.8rem', fontWeight: 'bold'}}>{newAlerts.length}</div>
              <div style={{fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase'}}>New Alerts</div>
            </div>

            <div className={`card stat-card ${viewFilter === 'ongoing' ? 'active-filter' : ''}`} 
              onClick={() => setViewFilter('ongoing')}
              style={{flex: 1, cursor: 'pointer', borderTop: viewFilter === 'ongoing' ? '4px solid var(--accent-blue)' : '4px solid transparent'}}>
              <Truck size={24} color="var(--accent-blue)"/>
              <div style={{fontSize: '1.8rem', fontWeight: 'bold'}}>{ongoingAlerts.length}</div>
              <div style={{fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase'}}>Ongoing Missions</div>
            </div>

            <div className={`card stat-card ${viewFilter === 'admitted' ? 'active-filter' : ''}`} 
              onClick={() => setViewFilter('admitted')}
              style={{flex: 1, cursor: 'pointer', borderTop: viewFilter === 'admitted' ? '4px solid #10b981' : '4px solid transparent'}}>
              <CheckCircle size={24} color="#10b981"/>
              <div style={{fontSize: '1.8rem', fontWeight: 'bold'}}>{admittedAlerts.length}</div>
              <div style={{fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase'}}>In Hospital</div>
            </div>
          </div>

          <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            {filteredAlerts.length === 0 ? (
              <div className="card" style={{textAlign: 'center', padding: '4rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.01)'}}>
                <Clock size={40} style={{opacity: 0.2, marginBottom: '1rem'}}/>
                <p>No cases in this category.</p>
              </div>
            ) : (
              filteredAlerts.map(patient => (
                <div key={patient.id} className="card alert-card critical" 
                  style={{
                    borderLeft: '4px solid' + (viewFilter === 'new' ? 'var(--accent-red)' : viewFilter === 'ongoing' ? 'var(--accent-blue)' : '#10b981'),
                    position: 'relative',
                    zIndex: openDropdown === patient.id ? 100 : 1,
                    overflow: 'visible'
                  }}>
                  <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                    <div>
                      <h3 style={{color: 'white', fontSize: '1.1rem'}}>🚨 {patient.severity} TRAUMA DETECTED</h3>
                      <p style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>Case ID: {patient.id.substring(0,12)} | {formatToIST(patient.created_at || patient.time)}</p>
                    </div>
                    <div style={{textAlign: 'right'}}>
                       {viewFilter === 'ongoing' && (
                         <div style={{fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--accent-red)'}}>
                          {patient.eta_minutes ? `ETA: ${patient.eta_minutes} MIN` : 'Calculating...'}
                         </div>
                       )}
                    </div>
                  </div>

                  <div style={{background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 8, marginBottom: '1rem'}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '8px'}}>
                      <MapPin size={14}/> <span>{patient.location}</span>
                    </div>
                    <div style={{display: 'flex', gap: '0.8rem'}}>
                      <span style={{background: '#8b5cf6', padding: '3px 10px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 'bold'}}>👥 {patient.impact_scale || 'Significant'} IMPACT</span>
                      <span style={{background: 'rgba(255,255,255,0.1)', padding: '3px 10px', borderRadius: 4, fontSize: '0.7rem'}}>
                        🚑 {patient.dispatched_ambulance_names?.length > 0 ? patient.dispatched_ambulance_names.join(', ') : 'Unit Pending'}
                      </span>
                    </div>
                  </div>

                  <div className="btn-group" style={{flexDirection: 'column', gap: '0.8rem'}}>
                    {viewFilter === 'new' && (
                      <div style={{position: 'relative'}}>
                        <label style={{fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 'bold', marginBottom: '0.5rem', display: 'block'}}>SELECT FLEET UNITS</label>
                        <div 
                          onClick={() => setOpenDropdown(openDropdown === patient.id ? null : patient.id)}
                          style={{
                            background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: 8, border: '1px solid var(--border)',
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer'
                          }}
                        >
                          <span style={{color: (selectedAmbs[patient.id] || []).length ? 'white' : 'var(--text-muted)'}}>
                            {(selectedAmbs[patient.id] || []).length 
                              ? `${(selectedAmbs[patient.id] || []).length} Units Selected` 
                              : "Select Available Ambulances..."}
                          </span>
                          <ChevronDown size={18} style={{transform: openDropdown === patient.id ? 'rotate(180deg)' : 'none', transition: '0.3s'}}/>
                        </div>

                        {openDropdown === patient.id && (
                          <div style={{
                            position: 'absolute', top: '100%', left: 0, right: 0, background: '#1a1d21', border: '1px solid var(--border)',
                            borderRadius: 8, marginTop: 4, zIndex: 100, maxHeight: 200, overflowY: 'auto', boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
                          }}>
                            {ambulances.filter(a => a.is_available).map(amb => (
                              <div 
                                key={amb.id} onClick={() => toggleAmbulance(patient.id, amb.id)}
                                style={{
                                  padding: '10px 15px', borderBottom: '1px solid rgba(255,255,255,0.05)', cursor: 'pointer',
                                  background: (selectedAmbs[patient.id] || []).includes(amb.id) ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                                  display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                                }}
                              >
                                <div>
                                  <div style={{fontWeight: 'bold', color: 'white'}}>{amb.unit_name}</div>
                                  <div style={{fontSize: '0.7rem', color: 'var(--text-muted)'}}>{amb.vehicle_type} | {amb.unit_code}</div>
                                </div>
                                {(selectedAmbs[patient.id] || []).includes(amb.id) && <CheckCircle size={16} color="var(--accent-blue)"/>}
                              </div>
                            ))}
                            {ambulances.filter(a => a.is_available).length === 0 && (
                              <div style={{padding: '20px', textAlign: 'center', color: 'var(--text-muted)'}}>No available units</div>
                            )}
                          </div>
                        )}

                        <button 
                          className="primary" style={{width: '100%', marginTop: '1rem', height: '45px'}} 
                          disabled={!(selectedAmbs[patient.id] || []).length}
                          onClick={() => { 
                            assignAmbulances(patient.id, selectedAmbs[patient.id], user?.id); 
                            setOpenDropdown(null);
                            setTimeout(fetchAmbulances, 500); 
                          }}>
                          Dispatch Selected Fleet
                        </button>
                      </div>
                    )}

                    {viewFilter === 'ongoing' && (
                      <button className="primary" style={{width: '100%', background: '#10b981'}} onClick={() => { updateHospitalStatus(patient.id, 'admitted'); setTimeout(fetchAmbulances, 500); }}>
                        Confirm Arrival & Admit to ICU
                      </button>
                    )}

                    {viewFilter === 'admitted' && (
                      <button className="outline" style={{width: '100%', borderColor: '#ef4444', color: '#ef4444'}} onClick={() => dischargePatient(patient.id)}>
                        <UserMinus size={18} style={{marginRight: 8}}/> Discharge Patient
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div>
          <div className="card" style={{height: '300px', padding: 0, overflow: 'hidden', marginBottom: '1.5rem'}}>
            <MapContainer center={[user?.lat || 31.5186, user?.lng || 75.9712]} zoom={13} style={{ height: '100%', width: '100%' }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <Marker position={[user?.lat || 31.5186, user?.lng || 75.9712]}><Popup>Hospital Base</Popup></Marker>
              {Object.entries(ambulanceLocations).map(([id, pos]) => (
                <Marker key={id} position={[pos.lat, pos.lng]} icon={ambulanceIcon}><Popup>Ambulance {id}</Popup></Marker>
              ))}
            </MapContainer>
          </div>

          <div className="card">
            <h3 style={{fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem'}}><Truck size={18}/> Fleet Status</h3>
            <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem'}}>
              {ambulances.map(amb => {
                const mission = alerts.find(a => a.dispatched_ambulance_names?.includes(amb.unit_name));
                return (
                  <div key={amb.id} style={{padding: '0.75rem', borderBottom: '1px solid var(--border)', fontSize: '0.85rem'}}>
                    <div style={{display: 'flex', justifyContent: 'space-between'}}>
                      <span style={{fontWeight: 'bold', color: 'white'}}>{amb.unit_name}</span>
                      <span style={{color: amb.is_available ? '#10b981' : '#ef4444', fontWeight: 'bold'}}>{amb.is_available ? 'AVAILABLE' : 'ON MISSION'}</span>
                    </div>
                    {!amb.is_available && mission && (
                      <div style={{marginTop: '5px', color: 'var(--text-muted)', fontSize: '0.7rem'}}>Case: {mission.id.substring(0, 8)}...</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
