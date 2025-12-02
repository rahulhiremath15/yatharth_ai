import React, { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { Orb } from './Components/Orb';
import { SatelliteFeed } from './Components/SatelliteFeed';
import axios from 'axios';
import './App.css';

function App() {
  const [claim, setClaim] = useState("");
  const [imageUrl, setImageUrl] = useState(""); // State for Image URL
  const [showImageInput, setShowImageInput] = useState(false); // Toggle for image input
  const [data, setData] = useState({ verdict: null, explanation: "", mood: "calm" });
  const [loading, setLoading] = useState(false);

  // Use your live Render Backend URL here
  const API_URL = "https://yatharth-backend.onrender.com";

  const handleSearch = async (e) => {
    if (e.key === 'Enter') {
      // Prevent searching if both fields are empty
      if (!claim.trim() && !imageUrl.trim()) return;

      setLoading(true);
      // Set temporary mood to 'thinking' (Gold color)
      setData({ ...data, mood: "thinking" });
      
      try {
        const res = await axios.post(`${API_URL}/analyze`, { 
            claim: claim,
            imageUrl: imageUrl 
        });
        setData(res.data);
      } catch (err) {
        console.error(err);
        setData({ 
          verdict: "ERROR", 
          explanation: "Connection to Orb interrupted. Please try again.", 
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
            <p>MULTI-MODAL TRUTH ENGINE</p>
          </header>

          <div className="search-container">
            {/* Main Text Input */}
            <input 
              type="text" 
              placeholder={showImageInput ? "Ask a question about the image..." : "Enter a rumor to consult the Orb..."}
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
              onKeyDown={handleSearch}
              disabled={loading}
            />

            {/* Conditional Image URL Input */}
            {showImageInput && (
                <input 
                  type="text" 
                  placeholder="Paste Image URL here..." 
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  onKeyDown={handleSearch}
                  disabled={loading}
                  style={{ 
                      marginTop: '15px', 
                      fontSize: '1rem', 
                      borderColor: '#00f0ff',
                      background: 'rgba(0, 240, 255, 0.1)' 
                  }}
                />
            )}

            {/* Toggle Button for Image Mode */}
            <div style={{ display: 'flex', justifyContent: 'center' }}>
                <button 
                    onClick={() => setShowImageInput(!showImageInput)}
                    style={{
                        background: 'transparent', 
                        border: 'none', 
                        color: '#666', 
                        marginTop: '15px', 
                        cursor: 'pointer', 
                        fontSize: '0.8rem', 
                        letterSpacing: '2px',
                        transition: 'color 0.3s'
                    }}
                    onMouseEnter={(e) => e.target.style.color = '#fff'}
                    onMouseLeave={(e) => e.target.style.color = '#666'}
                >
                    {showImageInput ? "✖ CLOSE IMAGE MODE" : "+ ANALYZE IMAGE"}
                </button>
            </div>
          </div>

          {/* Result Display */}
          {data.verdict && (
            <div className={`result-card ${data.mood || 'calm'}`}>
              <h2>{data.verdict.toUpperCase()}</h2>
              <p style={{ whiteSpace: 'pre-line' }}>{data.explanation}</p>
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