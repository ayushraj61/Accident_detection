import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, Hospital, Truck, Lock, Mail } from 'lucide-react';

export default function Login() {
  const [role, setRole] = useState('hospital');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password, role);
      if (role === 'admin') navigate('/');
      else if (role === 'hospital') navigate('/hospital');
      else navigate('/ambulance');
    } catch (err) {
      setError('Invalid credentials. Please try again.');
    }
  };

  return (
    <div className="dashboard-container" style={{maxWidth: 450, marginTop: '10vh'}}>
      <div className="card" style={{padding: '3rem'}}>
        <div style={{textAlign: 'center', marginBottom: '2rem'}}>
          <ShieldAlert size={48} color="var(--accent-blue)" style={{marginBottom: '1rem'}}/>
          <h1 style={{fontSize: '1.5rem', marginBottom: '0.5rem'}}>AI-AIDERS Portal</h1>
          <p style={{color: 'var(--text-muted)'}}>Secure access for emergency responders</p>
        </div>

        <div style={{display: 'flex', gap: '0.5rem', marginBottom: '2rem'}}>
          <button 
            className={role === 'admin' ? 'primary' : 'outline'}
            onClick={() => setRole('admin')}
            style={{flex: 1, padding: '10px 5px', fontSize: '0.75rem'}}
          >
            <ShieldAlert size={14} style={{marginRight: 4}}/> Command
          </button>
          <button 
            className={role === 'hospital' ? 'primary' : 'outline'}
            onClick={() => setRole('hospital')}
            style={{flex: 1, padding: '10px 5px', fontSize: '0.75rem'}}
          >
            <Hospital size={14} style={{marginRight: 4}}/> Hospital
          </button>
          <button 
            className={role === 'ambulance' ? 'primary' : 'outline'}
            onClick={() => setRole('ambulance')}
            style={{flex: 1, padding: '10px 5px', fontSize: '0.75rem'}}
          >
            <Truck size={14} style={{marginRight: 4}}/> Ambulance
          </button>
        </div>

        {error && <div style={{color: 'var(--accent-red)', marginBottom: '1rem', textAlign: 'center', fontSize: '0.9rem'}}>{error}</div>}

        <form onSubmit={handleSubmit} style={{display: 'flex', flexDirection: 'column', gap: '1.25rem'}}>
          <div style={{position: 'relative'}}>
            <Mail size={18} style={{position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)'}}/>
            <input 
              type={role === 'hospital' ? 'email' : 'text'}
              placeholder={
                role === 'admin' ? 'Admin Username' : 
                role === 'hospital' ? 'Hospital Email' : 
                'Ambulance Unit Code'
              }
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: '100%', padding: '0.75rem 0.75rem 0.75rem 2.5rem',
                background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)',
                borderRadius: 6, color: 'white'
              }}
            />
          </div>
          <div style={{position: 'relative'}}>
            <Lock size={18} style={{position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)'}}/>
            <input 
              type="password"
              placeholder="Password / Driver PIN"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%', padding: '0.75rem 0.75rem 0.75rem 2.5rem',
                background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)',
                borderRadius: 6, color: 'white'
              }}
            />
          </div>
          
          <button type="submit" className="primary" style={{marginTop: '0.5rem', padding: '1rem'}}>
            Sign In to Dashboard
          </button>
        </form>

        <div style={{textAlign: 'center', marginTop: '2rem', fontSize: '0.9rem'}}>
          <p style={{color: 'var(--text-muted)'}}>
            Don't have an account? <Link to="/register" style={{color: 'var(--accent-blue)', fontWeight: 600}}>Register Hospital</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
