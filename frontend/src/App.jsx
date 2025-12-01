import React, { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { Orb } from './Components/Orb';
import { SatelliteFeed } from './Components/SatelliteFeed';
import axios from 'axios';
import './App.css';

function App() {
  const [claim, setClaim] = useState("");
  const [data, setData] = useState({ verdict: null, explanation: "", mood: "calm" });
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    if (e.key === 'Enter' && claim.trim() !== "") {
      setLoading(true);
      // Set temporary mood to 'thinking' while we wait
      setData({ ...data, mood: "thinking" });
      
      try {
        const res = await axios.post('http://127.0.0.1:5000/analyze', { claim });
        setData(res.data);
      } catch (err) {
        console.error(err);
        setData({ 
          verdict: "ERROR", 
          explanation: "Connection to Orb interrupted.", 
          mood: "spikey" 
        });
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="main-wrapper">
      
      {/* 1. The 3D Scene Layer (Fixed Background) */}
      <div className="canvas-container">
        <Canvas camera={{ position: [0, 0, 6] }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1.5} color="#00f0ff" />
          <pointLight position={[-10, -10, -10]} intensity={1.5} color="#ff0055" />
          <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade />
          
          <Suspense fallback={null}>
            {/* Pass 'thinking' mood if loading, otherwise the result mood */}
            <Orb mood={loading ? "thinking" : data.mood} />
          </Suspense>
          
          <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
        </Canvas>
      </div>

      {/* 2. The Scrolling UI Layer */}
      <div className="content-scroll-layer">
        
        {/* Section A: Search & Orb Overlay */}
        <section className="hero-section">
          <header>
            <h1>YATHARTH</h1>
            <p>THE ORB OF CLARITY</p>
          </header>

          <div className="search-container">
            <input 
              type="text" 
              placeholder="Enter a rumor to consult the Orb..." 
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
              onKeyDown={handleSearch}
              disabled={loading}
            />
          </div>

          {data.verdict && (
            <div className={`result-card ${data.mood || 'calm'}`}>
              <h2>{data.verdict.toUpperCase()}</h2>
              <p>{data.explanation}</p>
            </div>
          )}

          <div className="scroll-indicator">
            <p>▼ LIVE INTELLIGENCE FEED ▼</p>
          </div>
        </section>

        {/* Section B: The Satellite Feed */}
        <section className="feed-section">
          <h2>GLOBAL MONITORING STATION</h2>
          <SatelliteFeed />
        </section>

      </div>
    </div>
  );
}

export default App;