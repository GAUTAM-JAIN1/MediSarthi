import React, { useState, useEffect } from 'react';
import { BsHospital, BsGeoAlt, BsWifi } from "react-icons/bs";

const Nearby_Hospital = () => {
  const [statusText, setStatusText] = useState("Initializing GPS...");
  const [foundCount, setFoundCount] = useState(0);

  // Simulate the "Scanning" process with changing text
  useEffect(() => {
    const statuses = [
      "Triangulating position...",
      "Pinging emergency networks...",
      "Analyzing traffic conditions...",
      "Filtering for ICU availability...",
      "Establishing connection..."
    ];

    let i = 0;
    const interval = setInterval(() => {
      if (i < statuses.length) {
        setStatusText(statuses[i]);
        i++;
      } else {
        // Once finished scanning, maybe show a result count
        setStatusText("Scan Complete. Waiting for user selection.");
        setFoundCount(3);
        clearInterval(interval);
      }
    }, 1200); // Change text every 1.2 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
        background: 'rgba(255, 255, 255, 0.03)', // Glass Background
        padding: '40px',
        borderRadius: '20px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(15px)',
        maxWidth: '350px',
        width: '100%',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
    }}>

      {/* --- CSS Animations --- */}
      <style>
        {`
          @keyframes radar-ping {
            0% { transform: scale(1); opacity: 0.8; border-width: 2px; }
            100% { transform: scale(3); opacity: 0; border-width: 0px; }
          }
          @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
          @keyframes spin-slow {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>

      {/* --- Header --- */}
      <h3 style={{ 
          color: '#ff6b6b', 
          margin: '0 0 40px 0', 
          letterSpacing: '2px', 
          fontSize: '1rem',
          display: 'flex', alignItems: 'center', gap: '10px'
      }}>
        <BsWifi style={{ animation: 'blink 1s infinite' }} /> 
        SEARCHING AREA
      </h3>

      {/* --- Radar Animation Container --- */}
      <div style={{ position: 'relative', width: '120px', height: '120px', marginBottom: '40px' }}>
        
        {/* The Central Icon */}
        <div style={{
            position: 'absolute', top: '0', left: '0', right: '0', bottom: '0',
            background: 'linear-gradient(135deg, #eb4d4b, #ff7979)',
            borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white',
            fontSize: '2.5rem',
            zIndex: 2,
            boxShadow: '0 0 20px rgba(235, 77, 75, 0.5)'
        }}>
            <BsHospital />
        </div>

        {/* Pulse Ring 1 */}
        <div style={{
            position: 'absolute', top: '0', left: '0', width: '100%', height: '100%',
            borderRadius: '50%',
            border: '2px solid #ff6b6b',
            animation: 'radar-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
            zIndex: 1
        }} />

        {/* Pulse Ring 2 (Delayed) */}
        <div style={{
            position: 'absolute', top: '0', left: '0', width: '100%', height: '100%',
            borderRadius: '50%',
            border: '2px solid #ff6b6b',
            animation: 'radar-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
            animationDelay: '1s',
            zIndex: 1
        }} />
        
      </div>

      {/* --- Status Text --- */}
      <div style={{ minHeight: '60px' }}>
        <h4 style={{ color: 'white', margin: '0 0 5px 0', fontSize: '1.1rem' }}>
            {statusText}
        </h4>
        <p style={{ color: '#888', fontSize: '0.85rem', margin: 0 }}>
            <BsGeoAlt style={{ marginRight: '5px', verticalAlign: 'middle' }} />
            {foundCount > 0 ? `${foundCount} Facilities Found` : "Scanning Radius: 5km"}
        </p>
      </div>

      {/* --- Progress Bar --- */}
      <div style={{ 
          width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', 
          marginTop: '20px', borderRadius: '2px', overflow: 'hidden' 
      }}>
          <div style={{
              height: '100%', width: '50%', background: '#ff6b6b',
              animation: 'slide 2s ease-in-out infinite'
          }} />
          <style>{`@keyframes slide { 0% {transform: translateX(-100%)} 100% {transform: translateX(200%)} }`}</style>
      </div>

    </div>
  );
};

export default Nearby_Hospital;