import React, { useState } from 'react';

const Call_Form = () => {
  const [formData, setFormData] = useState({
    number: '',
    disease: '',
    doctor_name: '',
    availability: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("Form Submitted:", formData);
    alert(`Calling Dr. ${formData.doctor_name} for ${formData.disease}...`);
    // Add your API call logic here
  };

  return (
    <form 
      onSubmit={handleSubmit} 
      style={{
        background: 'rgba(255, 255, 255, 0.03)', // Glass Background
        padding: '30px',
        borderRadius: '20px',
        border: '1px solid rgba(255, 255, 255, 0.1)', // Subtle border
        backdropFilter: 'blur(10px)', // The "Frost" effect
        maxWidth: '400px',
        width: '100%',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '15px',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
      }}
    >
      <h3 style={{ color: 'white', margin: '0 0 10px 0', textAlign: 'center' }}>
        Book Appointment
      </h3>

      <GlassInput 
        type="text"
        name="number" 
        placeholder="Phone (+91...)" 
        value={formData.number} 
        onChange={handleChange} 
        required
      />
      
      <GlassInput 
        type="text"
        name="disease" 
        placeholder="Disease / Symptoms" 
        value={formData.disease} 
        onChange={handleChange} 
        required
      />
      
      <GlassInput 
        type="text"
        name="doctor_name" 
        placeholder="Doctor Name" 
        value={formData.doctor_name} 
        onChange={handleChange} 
        required
      />
      
      <GlassInput 
        type="text"
        name="availability" 
        placeholder="Time Slot (e.g., 10:00 AM)" 
        value={formData.availability} 
        onChange={handleChange} 
        required
      />

      <button 
        type="submit" 
        style={{
          padding: '15px',
          borderRadius: '10px',
          border: 'none',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', // Purple/Blue Gradient
          color: 'white',
          fontSize: '1rem',
          fontWeight: 'bold',
          cursor: 'pointer',
          marginTop: '10px',
          transition: 'transform 0.2s, box-shadow 0.2s',
          boxShadow: '0 4px 15px rgba(118, 75, 162, 0.4)'
        }}
        onMouseEnter={(e) => {
          e.target.style.transform = 'scale(1.02)';
          e.target.style.boxShadow = '0 6px 20px rgba(118, 75, 162, 0.6)';
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = 'scale(1)';
          e.target.style.boxShadow = '0 4px 15px rgba(118, 75, 162, 0.4)';
        }}
      >
        Schedule Call
      </button>
    </form>
  );
};

// --- Helper Component for the Inputs ---
const GlassInput = (props) => {
  return (
    <input 
      {...props}
      style={{
        width: '100%',
        padding: '15px',
        borderRadius: '10px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        color: 'white',
        fontSize: '0.9rem',
        outline: 'none',
        transition: 'all 0.3s ease',
        boxSizing: 'border-box' // Prevents padding from breaking layout
      }}
      onFocus={(e) => {
        e.target.style.borderColor = '#667eea'; // Glow color on focus
        e.target.style.backgroundColor = 'rgba(0, 0, 0, 0.2)';
      }}
      onBlur={(e) => {
        e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
      }}
    />
  );
};

export default Call_Form;