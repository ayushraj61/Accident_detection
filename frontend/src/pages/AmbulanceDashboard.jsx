import React, { useEffect, useState, useRef } from 'react';
import { useAlerts } from '../context/AlertContext';
import { useAuth } from '../context/AuthContext';
import { Navigation, AlertTriangle, CheckCircle, Clock, MapPin, Map as MapIcon, Crosshair, ArrowUp, X, Move, ChevronRight, Navigation2, Building2 } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import 'leaflet-routing-machine';

// Fix Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const ambulanceIcon = (heading) => new L.DivIcon({
    html: `<div style="transform: rotate(${heading || 0}deg); transition: transform 0.5s ease;"><img src="https://cdn-icons-png.flaticon.com/512/1048/1048329.png" style="width:32px; height:32px;"/></div>`,
    className: 'custom-div-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
});

const accidentIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/564/564619.png',
    iconSize: [35, 35],
    iconAnchor: [17, 35],
});

const hospitalIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3063/3063200.png',
    iconSize: [35, 35],
    iconAnchor: [17, 35],
});

const destIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/684/684908.png',
    iconSize: [35, 35],
    iconAnchor: [17, 35],
});

// Import Routing Machine CSS and hide the default text panel
const routingCSS = document.createElement('link');
routingCSS.rel = 'stylesheet';
routingCSS.href = 'https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css';
document.head.appendChild(routingCSS);

const hideRoutingText = document.createElement('style');
hideRoutingText.innerHTML = '.leaflet-routing-container { display: none !important; }';
document.head.appendChild(hideRoutingText);

function RoutingMachine({ from, to, active, onRouteFound }) {
  const map = useMap();
  const routingControlRef = useRef(null);

  useEffect(() => {
    if (routingControlRef.current) { try { map.removeControl(routingControlRef.current); } catch(e) {} routingControlRef.current = null; }
    if (!map || !from || !to || !active) return;
    try {
        routingControlRef.current = L.Routing.control({
          waypoints: [L.latLng(from[0], from[1]), L.latLng(to[0], to[1])],
          router: L.Routing.osrmv1({ serviceUrl: 'https://router.project-osrm.org/route/v1', timeout: 15000 }),
          lineOptions: { styles: [{ color: '#3b82f6', weight: 6, opacity: 0.8 }] },
          addWaypoints: false, draggableWaypoints: false, show: false, fitSelectedRoutes: true
        }).on('routesfound', function(e) {
          const summary = e.routes[0].summary;
          onRouteFound({ distance: (summary.totalDistance / 1000).toFixed(1), time: Math.round(summary.totalTime / 60) });
        }).addTo(map);
    } catch (err) {}
    return () => { if (routingControlRef.current) { try { map.removeControl(routingControlRef.current); } catch(e) {} } };
  }, [map, from, JSON.stringify(to), active]);
  return null;
}

function MapControl({ center, active, isNavigating }) {
  const map = useMap();
  useEffect(() => { if (active) map.setView(center, isNavigating ? 17 : map.getZoom(), { animate: true }); }, [center, active, isNavigating]);
  return null;
}

export default function AmbulanceDashboard() {
  const { alerts, updateAmbulanceStatus } = useAlerts();
  const { user } = useAuth();
  const [currentPos, setCurrentPos] = useState([user?.lat || 28.6139, user?.lng || 77.2090]);
  const [heading, setHeading] = useState(0);
  const [gpsStatus, setGpsStatus] = useState('offline');
  const [autoCenter, setAutoCenter] = useState(true);
  const [routeInfo, setRouteInfo] = useState({ distance: '0.0', time: '0' });
  const watchIdRef = useRef(null);

  useEffect(() => {
    if (!navigator.geolocation) return;
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude, heading: geoHeading } = pos.coords;
        setCurrentPos(prev => {
            const angle = Math.atan2(longitude - prev[1], latitude - prev[0]) * 180 / Math.PI;
            setHeading(geoHeading || angle);
            return [latitude, longitude];
        });
        setGpsStatus('active');
        axios.post('http://localhost:8000/api/v1/emergency/update-location', {
          ambulance_id: user.id, lat: latitude, lng: longitude
        }).catch(() => {});
      },
      () => setGpsStatus('error'),
      { enableHighAccuracy: true, maximumAge: 0, timeout: 20000 }
    );
    return () => { if (watchIdRef.current) navigator.geolocation.clearWatch(watchIdRef.current); };
  }, [user.id]);

  const activeAlert = alerts.find(a => a.hospital_id === user?.hospital_id && a.ambulanceStatus !== 'cleared');
  const driverStatus = activeAlert ? activeAlert.ambulanceStatus : 'idle';
  
  // Logic to handle 0 distance when at scene or hospital
  // IST Formatter Utility
  const formatToIST = (dateString) => {
    if (!dateString) return '--:--:--';
    return new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    }).format(new Date(dateString));
  };

  useEffect(() => {
    if (!activeAlert || !routeInfo.time || routeInfo.time === '0') return;
    
    // Sync ETA with backend every time it changes
    const syncETA = async () => {
      try {
        await axios.post(`http://localhost:8000/api/v1/emergency/incident/${activeAlert.id}/eta?eta=${routeInfo.time}`);
      } catch (err) {}
    };
    
    const timer = setTimeout(syncETA, 2000); // Debounce to avoid spamming
    return () => clearTimeout(timer);
  }, [routeInfo.time, activeAlert?.id]);

  const handleStatusUpdate = (alertId, newStatus) => {
    updateAmbulanceStatus(alertId, newStatus);
    if (newStatus === 'onscene' || newStatus === 'arrived_hospital') {
      setRouteInfo({ distance: '0.0', time: '0' });
    }
  };

  const isNavigating = ['enroute', 'onscene', 'enroute_hospital', 'arrived_hospital'].includes(driverStatus);
  const isReturning = ['enroute_hospital', 'arrived_hospital'].includes(driverStatus);
  
  const hospitalCoords = [user?.hospital_lat || 28.6139, user?.hospital_lng || 77.2090];
  const destination = isReturning ? hospitalCoords : activeAlert ? [activeAlert.locationRaw.lat, activeAlert.locationRaw.lng] : null;
  const destName = isReturning ? user?.hospital_name || "City General Hospital" : activeAlert?.location?.split(',')[0];

  return (
    <div className="dashboard-container" style={{padding: '15px', height: '100vh', boxSizing: 'border-box', background: '#0a0b0d', display: 'flex', flexDirection: 'column', gap: '15px'}}>
      
      {/* 🟢 NAVIGATION OVERLAY */}
      {isNavigating && (
        <div style={{
          position: 'absolute', top: 30, left: '50%', transform: 'translateX(-50%)', zIndex: 1000,
          background: isReturning ? '#1e40af' : '#065f46', color: 'white', padding: '16px 24px', borderRadius: '16px',
          boxShadow: '0 12px 48px rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', gap: '1.5rem', 
          width: '90%', maxWidth: '500px', border: '1px solid rgba(255,255,255,0.2)'
        }}>
          <div style={{background: 'rgba(255,255,255,0.2)', padding: '12px', borderRadius: '12px'}}>
            {isReturning ? <Building2 size={32}/> : <Navigation2 size={32} style={{transform: 'rotate(45deg)'}}/>}
          </div>
          <div style={{flex: 1}}>
            <div style={{fontSize: '0.8rem', opacity: 0.8, fontWeight: 'bold', textTransform: 'uppercase'}}>
                {isReturning ? 'Returning to Base' : 'Directing to Scene'}
            </div>
            <div style={{fontSize: '1.4rem', fontWeight: 'bold'}}>{destName}</div>
          </div>
          <div style={{textAlign: 'right', borderLeft: '1px solid rgba(255,255,255,0.2)', paddingLeft: '20px'}}>
             <div style={{fontSize: '1.8rem', fontWeight: 'bold'}}>{routeInfo.time}</div>
             <div style={{fontSize: '0.7rem', opacity: 0.8}}>MINS</div>
          </div>
        </div>
      )}

      <div style={{flex: 1, display: 'grid', gridTemplateColumns: '1fr 350px', gap: '15px', overflow: 'hidden'}}>
        
        <div className="card" style={{padding: 0, overflow: 'hidden', position: 'relative', border: '1px solid var(--border)', borderRadius: '20px', background: '#111827'}}>
          <MapContainer center={currentPos} zoom={15} style={{ height: '100%', width: '100%' }} zoomControl={false}>
            <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
            <MapControl center={currentPos} active={autoCenter} isNavigating={isNavigating} />
            
            <RoutingMachine 
                from={currentPos} 
                to={destination} 
                active={isNavigating || driverStatus === 'dispatched'} 
                onRouteFound={setRouteInfo} 
            />

            {activeAlert && (
                <>
                    <Marker position={destination} icon={destIcon}><Popup>DESTINATION: {destName}</Popup></Marker>
                    {!isReturning && <Marker position={hospitalCoords} icon={hospitalIcon} opacity={0.5}/>}
                    {isReturning && <Marker position={[activeAlert.locationRaw.lat, activeAlert.locationRaw.lng]} icon={accidentIcon} opacity={0.5}/>}
                </>
            )}
            
            <Marker position={currentPos} icon={ambulanceIcon(heading)}/>

            <button onClick={() => setAutoCenter(!autoCenter)} style={{
                position: 'absolute', bottom: '20px', left: '20px', zIndex: 1000,
                background: autoCenter ? '#3b82f6' : 'white', color: autoCenter ? 'white' : 'black', 
                border: 'none', borderRadius: '50%', width: '50px', height: '50px', 
                display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 15px rgba(0,0,0,0.3)'
            }}> <Navigation size={24} fill="currentColor"/> </button>
          </MapContainer>
        </div>

        <div style={{display: 'flex', flexDirection: 'column', gap: '15px'}}>
           
           <div className="card" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#111827', padding: '12px 20px'}}>
              <h1 style={{fontSize: '1.1rem', margin: 0}}>{user?.unit_name}</h1>
              <div style={{width: 10, height: 10, borderRadius: '50%', background: gpsStatus === 'active' ? '#10b981' : '#f59e0b'}}></div>
           </div>

           {!activeAlert ? (
             <div className="card" style={{flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', textAlign: 'center', background: 'rgba(255,255,255,0.02)', border: '1px dashed var(--border)'}}>
                <Navigation2 size={48} style={{margin: '0 auto 1.5rem', opacity: 0.1}}/>
                <h3 style={{fontSize: '0.9rem', color: 'var(--text-muted)'}}>Standing by for Dispatches</h3>
             </div>
           ) : (
             <div style={{display: 'flex', flexDirection: 'column', gap: '15px', flex: 1}}>
                <div className="card" style={{borderLeft: '4px solid #ef4444', background: isReturning ? 'rgba(30, 64, 175, 0.05)' : 'rgba(239, 68, 68, 0.05)'}}>
                   <div style={{fontSize: '0.7rem', color: isReturning ? '#3b82f6' : '#ef4444', fontWeight: 'bold', marginBottom: '0.5rem'}}>
                       {isReturning ? 'HOSPITAL INBOUND' : 'ACTIVE EMERGENCY'}
                   </div>
                   <h2 style={{fontSize: '1.1rem', marginBottom: '0.3rem'}}>
                       {isReturning ? `🏥 ${user?.hospital_name || "City General"}` : `🚨 ${activeAlert.severity} ACCIDENT`}
                   </h2>
                   <p style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem'}}>
                       {isReturning ? 'Emergency Trauma Center' : activeAlert.location}
                   </p>
                   
                   <button 
                     onClick={() => window.open(`https://www.google.com/maps/dir/?api=1&origin=${currentPos[0]},${currentPos[1]}&destination=${destination[0]},${destination[1]}&travelmode=driving`, '_blank')}
                     style={{
                       width: '100%', background: '#4285F4', color: 'white', border: 'none', padding: '10px', borderRadius: '8px', fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', cursor: 'pointer'
                     }}
                   >
                     <img src="https://cdn-icons-png.flaticon.com/512/2991/2991148.png" style={{width: 18}} alt="G"/>
                     NAVIGATE TO {isReturning ? 'HOSPITAL' : 'SCENE'}
                   </button>
                                <div className="card" style={{flex: 1}}>
                   <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                      {[
                        { step: 1, label: 'Accept Call', done: isNavigating, active: driverStatus === 'dispatched' },
                        { step: 2, label: 'Arrive at Scene', done: driverStatus === 'onscene' || isReturning, active: driverStatus === 'enroute' },
                        { step: 3, label: 'Load Patient', done: isReturning, active: driverStatus === 'onscene' },
                        { step: 4, label: 'At Hospital', done: driverStatus === 'arrived_hospital', active: driverStatus === 'enroute_hospital' }
                      ].map(s => (
                        <div key={s.step} style={{display: 'flex', alignItems: 'center', gap: '1rem', opacity: s.active ? 1 : s.done ? 0.6 : 0.2}}>
                           <div style={{width: 24, height: 24, borderRadius: '50%', background: s.done ? '#10b981' : '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '0.7rem'}}>
                              {s.done ? <CheckCircle size={14}/> : s.step}
                           </div>
                           <span style={{fontSize: '0.85rem', fontWeight: s.active ? 'bold' : 'normal'}}>{s.label}</span>
                        </div>
                      ))}
                   </div>

                   <div style={{marginTop: '2rem'}}>
                      {(driverStatus === 'idle' || driverStatus === 'dispatched') && <button className="primary" style={{width: '100%', padding: '15px'}} onClick={() => handleStatusUpdate(activeAlert.id, 'enroute')}>START NAVIGATION</button>}
                      {driverStatus === 'enroute' && <button className="primary" style={{width: '100%', padding: '15px', background: '#3b82f6'}} onClick={() => handleStatusUpdate(activeAlert.id, 'onscene')}>I HAVE ARRIVED AT SCENE</button>}
                      {driverStatus === 'onscene' && <button className="primary" style={{width: '100%', padding: '15px', background: '#8b5cf6'}} onClick={() => handleStatusUpdate(activeAlert.id, 'enroute_hospital')}>PATIENT LOADED: TO HOSPITAL</button>}
                      {driverStatus === 'enroute_hospital' && <button className="primary" style={{width: '100%', padding: '15px', background: '#1e40af'}} onClick={() => handleStatusUpdate(activeAlert.id, 'arrived_hospital')}>ARRIVED AT HOSPITAL</button>}
                      {driverStatus === 'arrived_hospital' && <button className="primary" style={{width: '100%', padding: '15px', background: '#10b981'}} onClick={() => handleStatusUpdate(activeAlert.id, 'cleared')}>MISSION COMPLETE</button>}
                   </div>
                </div>
  </div>
             </div>
           )}

           <div className="card" style={{padding: '1.2rem', display: 'flex', gap: '2rem', background: '#111827'}}>
                <div style={{flex: 1}}>
                   <div style={{fontSize: '1.6rem', fontWeight: 'bold', color: '#10b981'}}>{routeInfo.time}</div>
                   <div style={{fontSize: '0.6rem', color: 'var(--text-muted)', fontWeight: 'bold'}}>MINUTES</div>
                </div>
                <div style={{flex: 1, borderLeft: '1px solid var(--border)', paddingLeft: '1.5rem'}}>
                   <div style={{fontSize: '1.6rem', fontWeight: 'bold', color: 'white'}}>{routeInfo.distance}</div>
                   <div style={{fontSize: '0.6rem', color: 'var(--text-muted)', fontWeight: 'bold'}}>KILOMETERS</div>
                </div>
           </div>
        </div>
      </div>
    </div>
  );
}
