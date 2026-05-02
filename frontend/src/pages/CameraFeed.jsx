import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, Play, CheckCircle, Video } from 'lucide-react';

export default function CameraFeed() {
  const [mode, setMode] = useState('upload'); // 'upload' or 'webcam'
  const [file, setFile] = useState(null);
  const [lat, setLat] = useState("0.0");
  const [lng, setLng] = useState("0.0");

  useEffect(() => {
    detectLocation();
  }, []);

  const detectLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        setLat(pos.coords.latitude.toFixed(6));
        setLng(pos.coords.longitude.toFixed(6));
      }, (err) => console.error("Geolocation error", err));
    }
  };
  const [isUploading, setIsUploading] = useState(false);
  const [systemAlert, setSystemAlert] = useState("");
  const [isRecording, setIsRecording] = useState(false);

  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  // Turn off webcam if navigating away or switching modes
  useEffect(() => {
    if (mode === 'upload' && streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  }, [mode]);

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error(err);
      setSystemAlert("Could not access webcam. Please allow camera permissions.");
    }
  };

  const startEndlessSurveillance = async () => {
    
    setIsUploading(true);
    setSystemAlert("Hardware edge node is booting up natively on your Mac...");

    const formData = new FormData();
    formData.append("lat", lat);
    formData.append("lng", lng);

    try {
      const response = await fetch("http://localhost:8000/api/v1/emergency/start-edge-camera", {
        method: "POST",
        body: formData
      });
      setSystemAlert("24/7 Live Edge Camera active! A native popup window has opened. Go directly to the Central Command tab to wait for triggers.");
    } catch (err) {
      console.error(err);
      setSystemAlert("Error reaching the backend logic server. Is Uvicorn running?");
    }
    setIsUploading(false);
  };

  const triggerBackendPipeline = async (mediaBlob, filename) => {
    setIsUploading(true);
    setSystemAlert("");

    const formData = new FormData();
    formData.append("file", mediaBlob, filename);
    formData.append("lat", lat);
    formData.append("lng", lng);

    try {
      const response = await fetch("http://localhost:8000/api/v1/emergency/upload-video", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      setSystemAlert("Upload complete! YOLO AI pipeline is actively scanning the video Buffer...");
    } catch (err) {
      console.error(err);
      setSystemAlert("Error reaching the backend logic server. Is Uvicorn running?");
    }

    setIsUploading(false);
  };

  return (
    <div className="dashboard-container">
      <div className="header">
        <h1>Edge CCTV Node Configuration (Demo Sandbox)</h1>
        <div style={{display: 'flex', gap: '1rem'}}>
          <button 
            onClick={() => setMode('upload')} 
            style={{background: mode === 'upload' ? 'var(--accent-blue)' : 'var(--bg-dark)', border: 'none', color: 'white', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer'}}>
             <Upload size={16} style={{marginRight: 6}}/> Upload Dashcam
          </button>
          <button 
            onClick={() => { setMode('webcam'); startWebcam(); }} 
            style={{background: mode === 'webcam' ? 'var(--accent-blue)' : 'var(--bg-dark)', border: 'none', color: 'white', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer'}}>
             <Video size={16} style={{marginRight: 6}}/> Live Webcam
          </button>
        </div>
      </div>

      <div className="card" style={{maxWidth: '800px', margin: '0 auto', textAlign: 'center', padding: '3rem'}}>
        
        {mode === 'upload' ? (
           <Camera size={64} style={{color: 'var(--text-muted)', margin: '0 auto 2rem'}} />
        ) : (
           <div style={{background: 'black', borderRadius: '8px', overflow: 'hidden', marginBottom: '2rem'}}>
             <video ref={videoRef} autoPlay muted playsInline style={{width: '100%', maxHeight: '400px', objectFit: 'cover'}} />
           </div>
        )}

        <h2 style={{marginBottom: '1rem'}}>{mode === 'upload' ? 'Trigger Accident Simulation' : 'Live Camera Detection Feed'}</h2>
        
        <p style={{color: 'var(--text-muted)', marginBottom: '2rem'}}>
          {mode === 'upload' 
            ? 'Upload a dashcam MP4 file and spoof the exact GPS location of the "accident". The backend will calculate the dispatch against the mock Hospital databases!'
            : 'Looking directly into the live camera feed. Press the capture button to record 5 seconds of live footage and pass it directly into the dispatch AI!'}
        </p>

        <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem', alignItems: 'center'}}>
          
          <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem', width: '100%', alignItems: 'center'}}>
            <button 
              type="button" 
              onClick={detectLocation}
              style={{padding: '5px 10px', fontSize: '0.7rem', background: 'transparent', border: '1px solid var(--accent-blue)', color: 'var(--accent-blue)', borderRadius: 4, cursor: 'pointer'}}
            >
              Update Current GPS Location
            </button>
            <div style={{display: 'flex', gap: '1rem', width: '100%', justifyContent: 'center'}}>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start'}}>
                 <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.3rem'}}>Latitude</label>
                 <input type="number" step="0.0001" value={lat} onChange={e => setLat(e.target.value)} style={{padding: '0.8rem', borderRadius: '4px', background: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border)'}} />
              </div>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start'}}>
                 <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.3rem'}}>Longitude</label>
                 <input type="number" step="0.0001" value={lng} onChange={e => setLng(e.target.value)} style={{padding: '0.8rem', borderRadius: '4px', background: 'var(--bg-dark)', color: 'white', border: '1px solid var(--border)'}} />
              </div>
            </div>
          </div>
          
          {mode === 'upload' ? (
            <>
              <input type="file" accept="video/mp4" style={{display: 'none'}} id="video-upload" onChange={(e) => setFile(e.target.files[0])} />
              <label htmlFor="video-upload" style={{
                background: 'var(--bg-dark)', border: '2px dashed var(--accent-blue)', width: '60%',
                padding: '1rem 3rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', gap: '1rem', alignItems: 'center', justifyContent: 'center'
              }}>
                <Upload size={20} color="var(--accent-blue)"/>
                {file ? file.name : "Select MP4 Crash Footage"}
              </label>

              <button className="primary" disabled={!file || isUploading} onClick={() => triggerBackendPipeline(file, file.name)} style={{marginTop: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', width: '60%'}}>
                <Play size={20} />
                {isUploading ? "Uploading & Scanning..." : "Run AI Pipeline"}
              </button>
            </>
          ) : (
            <button className="primary" disabled={isUploading} onClick={startEndlessSurveillance} style={{marginTop: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', width: '60%', background: 'var(--accent-blue)'}}>
                <Camera size={20} />
                Deploy Endless Live Surveillance
            </button>
          )}

        </div>

        {systemAlert && (
          <div style={{marginTop: '2rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', padding: '1rem', borderRadius: '8px', color: '#10b981', display: 'flex', gap: '1rem', justifyContent: 'center'}}>
            <CheckCircle size={20} />
            {systemAlert}
            <br/>Open the Central Command tab to see it flash!
          </div>
        )}
      </div>
    </div>
  );
}
