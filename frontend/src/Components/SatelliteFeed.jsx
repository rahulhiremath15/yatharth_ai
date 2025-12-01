// frontend/src/Components/SatelliteFeed.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './SatelliteFeed.css';

export function SatelliteFeed() {
  const [feed, setFeed] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFeed = async () => {
      try {
        // Connect to your Flask backend
        const res = await axios.get('http://127.0.0.1:5000/feed');
        setFeed(res.data);
      } catch (err) {
        console.error("Feed signal lost:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchFeed();
  }, []);

  if (loading) return <div className="feed-loading">Scanning Global Networks...</div>;

  return (
    <div className="satellite-grid">
      {feed.map((item, index) => (
        <div key={index} className={`satellite-card ${item.mood || 'calm'}`}>
          <div className="satellite-header">
            <span className="signal-dot"></span>
            <span className="verdict">{item.verdict ? item.verdict.toUpperCase() : "ANALYZED"}</span>
          </div>
          <p className="claim-text">{item.claim}</p>
        </div>
      ))}
    </div>
  );
}