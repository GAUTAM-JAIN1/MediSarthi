import React, { useState } from 'react';
import { BsMic, BsMicMute, BsSoundwave } from "react-icons/bs";

const Record_Form = ({ onClose }) => {
  const [isRecording, setIsRecording] = useState(false);

  const toggleRecording = () => {
    if (!isRecording) {
      // Start Recording Logic
      console.log("Started recording...");
      setIsRecording(true);
    } else {
      // Stop Recording Logic
      console.log("Stopped recording.");
      setIsRecording(false);
      // alert("Recording saved! Processing..."); 
    }
  };

  return (
    <div style={{
        position: 'relative',
        background: 'rgba(255, 255, 255, 0.03)', // Glass Background
        padding: '40px',
        borderRadius: '20px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(15px)', // Heavy frost effect
        maxWidth: '350px',
        width: '100%',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        textAlign: 'center',
        overflow: 'hidden'
    }}>
      
      {/* Inject Keyframe Styles for the Pulse Animation */}
      <style>
        {`
          @keyframes pulse-ring {
            0% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(238, 82, 83, 0.7); }
            70% { transform: scale(1.1); box-shadow: 0 0 0 20px rgba(238, 82, 83, 0); }
            100% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(238, 82, 83, 0); }
          }
          @keyframes wave {
            0% { height: 10px; }
            50% { height: 30px; }
            100% { height: 10px; }
          }
        `}
      </style>

      {/* Header / Status Text */}
      <h3 style={{ 
          color: isRecording ? '#ff6b6b' : 'white', 
          marginBottom: '30px',
          fontWeight: '600',
          letterSpacing: '1px',
          transition: 'color 0.3s ease'
      }}>
        {isRecording ? "LISTENING..." : "Treat Symptom"}
      </h3>

      {/* Main Mic Button */}
      <button 
        onClick={toggleRecording}
        style={{
          position: 'relative',
          width: '100px',
          height: '100px',
          borderRadius: '50%',
          border: 'none',
          background: isRecording 
            ? 'linear-gradient(145deg, #ff6b6b, #ee5253)' // Red when recording
            : 'linear-gradient(145deg, #30336b, #130f40)', // Dark Blue when idle
          color: 'white',
          fontSize: '2.5rem',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          cursor: 'pointer',
          outline: 'none',
          boxShadow: isRecording 
            ? '0 0 30px rgba(238, 82, 83, 0.6)' 
            : '0 10px 20px rgba(0,0,0,0.3)',
          transition: 'all 0.3s ease',
          animation: isRecording ? 'pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite' : 'none'
        }}
      >
        {isRecording ? <BsMic /> : <BsMicMute />}
      </button>

      {/* Audio Visualizer Simulation */}
      <div style={{
          height: '40px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginTop: '30px',
          gap: '5px',
          opacity: isRecording ? 1 : 0.2, // Dim when not recording
          transition: 'opacity 0.3s'
      }}>
          {[...Array(5)].map((_, i) => (
              <div key={i} style={{
                  width: '4px',
                  height: '20px',
                  borderRadius: '2px',
                  background: isRecording ? '#ff6b6b' : '#555',
                  animation: isRecording ? `wave 1s ease-in-out infinite ${i * 0.1}s` : 'none'
              }} />
          ))}
      </div>

      <p style={{ color: '#888', fontSize: '0.8rem', marginTop: '10px' }}>
          {isRecording ? "Tap to stop" : "Tap to speak"}
      </p>

    </div>
  );
};

export default Record_Form;