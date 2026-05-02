import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, MapPin, Hospital, Bed, Activity, Lock, Mail, Phone } from 'lucide-react';

export default function RegisterHospital() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '', password: '', name: '', phone: '', address: '', city: '', state: '',
    lat: 28.6139, lng: 77.2090, total_beds: 50, icu_beds: 10, trauma_level: 'Level I',
    specialties: ['Trauma'], er_capacity: 30
  });

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'number' ? parseFloat(value) : value)
    }));
  };

  const handleSpecialtyToggle = (spec) => {
    setFormData(prev => ({
      ...prev,
      specialties: prev.specialties.includes(spec)
        ? prev.specialties.filter(s => s !== spec)
        : [...prev.specialties, spec]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post('http://localhost:8000/api/v1/auth/register/hospital', formData);
      alert('Registration successful! Please login.');
      navigate('/login');
    } catch (err) {
      alert('Registration failed. Email might already exist.');
    } finally {
      setLoading(false);
    }
  };

  const specialtiesList = ['Trauma', 'Burn Center', 'Neuro', 'Cardiac', 'Orthopedic', 'Pediatric', 'General'];

  return (
    <div className="dashboard-container" style={{maxWidth: 700}}>
      <div className="card" style={{padding: '3rem'}}>
        <div style={{textAlign: 'center', marginBottom: '2.5rem'}}>
          <Hospital size={40} color="var(--accent-blue)" style={{marginBottom: '1rem'}}/>
          <h1 style={{fontSize: '1.8rem', marginBottom: '0.5rem'}}>Register New Hospital</h1>
          <p style={{color: 'var(--text-muted)'}}>Join the AI-AIDERS emergency network</p>
          
          <div style={{display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '1.5rem'}}>
             {[1, 2, 3].map(s => (
               <div key={s} style={{
                 width: 30, height: 30, borderRadius: '50%',
                 background: step >= s ? 'var(--accent-blue)' : 'var(--border)',
                 display: 'flex', alignItems: 'center', justifyCenter: 'center',
                 fontSize: '0.8rem', fontWeight: 'bold', transition: 'all 0.3s'
               }}>{s}</div>
             ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
          
          {step === 1 && (
            <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
              <h3 style={{color: 'var(--accent-blue)', fontSize: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem'}}>Account Credentials</h3>
              <div className="grid-2">
                <input name="name" placeholder="Hospital Full Name" value={formData.name} onChange={handleChange} required className="form-input"/>
                <input name="email" type="email" placeholder="Email Address" value={formData.email} onChange={handleChange} required className="form-input"/>
                <input name="password" type="password" placeholder="Create Password" value={formData.password} onChange={handleChange} required className="form-input"/>
                <input name="phone" placeholder="Emergency Phone" value={formData.phone} onChange={handleChange} required className="form-input"/>
              </div>
              <button type="button" className="primary" onClick={() => setStep(2)}>Next: Location Details</button>
            </div>
          )}

          {step === 2 && (
            <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <h3 style={{color: 'var(--accent-blue)', fontSize: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', flex: 1}}>Location & GPS</h3>
                <button 
                  type="button" 
                  onClick={() => {
                    navigator.geolocation.getCurrentPosition((pos) => {
                      setFormData(prev => ({...prev, lat: pos.coords.latitude, lng: pos.coords.longitude}));
                    });
                  }}
                  style={{padding: '5px 10px', fontSize: '0.7rem', marginBottom: 5}}
                  className="outline"
                >
                  <MapPin size={12}/> Detect My Location
                </button>
              </div>
              <input name="address" placeholder="Street Address" value={formData.address} onChange={handleChange} required className="form-input"/>
              <div className="grid-2">
                <input name="city" placeholder="City" value={formData.city} onChange={handleChange} required className="form-input"/>
                <input name="state" placeholder="State" value={formData.state} onChange={handleChange} required className="form-input"/>
                <div style={{position: 'relative'}}>
                  <MapPin size={16} style={{position: 'absolute', left: 10, top: 12, color: 'var(--accent-blue)'}}/>
                  <input name="lat" type="number" step="any" placeholder="Latitude" value={formData.lat} onChange={handleChange} required className="form-input" style={{paddingLeft: '2.5rem'}}/>
                </div>
                <div style={{position: 'relative'}}>
                  <MapPin size={16} style={{position: 'absolute', left: 10, top: 12, color: 'var(--accent-blue)'}}/>
                  <input name="lng" type="number" step="any" placeholder="Longitude" value={formData.lng} onChange={handleChange} required className="form-input" style={{paddingLeft: '2.5rem'}}/>
                </div>
              </div>
              <p style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>* Coordinates are vital for accident matching. Use Google Maps to find your lat/lng.</p>
              <div className="btn-group">
                <button type="button" className="outline" onClick={() => setStep(1)}>Back</button>
                <button type="button" className="primary" onClick={() => setStep(3)}>Next: Clinical Capacity</button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div style={{display: 'flex', flexDirection: 'column', gap: '1.25rem'}}>
              <h3 style={{color: 'var(--accent-blue)', fontSize: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem'}}>Facility Capacity</h3>
              <div className="grid-2">
                <div className="form-group">
                  <label style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>Total ER Beds</label>
                  <input name="total_beds" type="number" value={formData.total_beds} onChange={handleChange} className="form-input"/>
                </div>
                <div className="form-group">
                  <label style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>ICU Beds</label>
                  <input name="icu_beds" type="number" value={formData.icu_beds} onChange={handleChange} className="form-input"/>
                </div>
                <div className="form-group">
                  <label style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>Trauma Level</label>
                  <select name="trauma_level" value={formData.trauma_level} onChange={handleChange} className="form-input">
                    <option>Level I</option><option>Level II</option><option>Level III</option><option>Level IV</option>
                  </select>
                </div>
                <div className="form-group">
                  <label style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>Max ER Capacity</label>
                  <input name="er_capacity" type="number" value={formData.er_capacity} onChange={handleChange} className="form-input"/>
                </div>
              </div>

              <div>
                <label style={{fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.5rem'}}>Specialties</label>
                <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
                  {specialtiesList.map(s => (
                    <div 
                      key={s} 
                      onClick={() => handleSpecialtyToggle(s)}
                      style={{
                        padding: '5px 12px', borderRadius: 20, fontSize: '0.8rem', cursor: 'pointer',
                        background: formData.specialties.includes(s) ? 'var(--accent-blue)' : 'rgba(255,255,255,0.05)',
                        border: '1px solid', borderColor: formData.specialties.includes(s) ? 'var(--accent-blue)' : 'var(--border)',
                        color: formData.specialties.includes(s) ? 'white' : 'var(--text-muted)',
                        transition: '0.2s'
                      }}
                    >{s}</div>
                  ))}
                </div>
              </div>

              <div className="btn-group">
                <button type="button" className="outline" onClick={() => setStep(2)}>Back</button>
                <button type="submit" className="primary" disabled={loading}>
                  {loading ? 'Processing...' : 'Complete Registration'}
                </button>
              </div>
            </div>
          )}
        </form>
      </div>
      
      <style>{`
        .form-input {
          width: 100%; padding: 0.75rem; background: rgba(255,255,255,0.03);
          border: 1px solid var(--border); borderRadius: 6px; color: white;
          font-family: inherit;
        }
        .form-input:focus { outline: none; border-color: var(--accent-blue); }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
      `}</style>
    </div>
  );
}
