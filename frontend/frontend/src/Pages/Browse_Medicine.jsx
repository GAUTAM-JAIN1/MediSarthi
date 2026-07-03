import React, { useState, useRef } from 'react';
import { BsPlus, BsX, BsFolder2Open, BsCapsule } from "react-icons/bs";

const Browse_Medicine = () => {
  const [medicines, setMedicines] = useState([]);
  const [currentInput, setCurrentInput] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  // --- Handlers ---

  const handleBrowseClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file.name);
      // Simulate extracting medicines from the file
      setTimeout(() => {
        setMedicines(prev => [...prev, "Extracted-Med-A", "Extracted-Med-B"]);
      }, 1000);
    }
  };

  const addMedicine = (e) => {
    e.preventDefault();
    if (currentInput.trim()) {
      setMedicines([...medicines, currentInput.trim()]);
      setCurrentInput("");
    }
  };

  const removeMedicine = (index) => {
    setMedicines(medicines.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    console.log("Submitting List:", medicines, "File:", selectedFile);
    alert(`Processing ${medicines.length} medicines...`);
  };

  return (
    <div style={{
        background: 'rgba(255, 255, 255, 0.03)', // Glass Background
        padding: '30px',
        borderRadius: '20px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(15px)',
        maxWidth: '400px',
        width: '100%',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        fontFamily: "'Inter', sans-serif"
    }}>
      
      <h3 style={{ 
          color: 'white', margin: 0, textAlign: 'center', letterSpacing: '1px',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' 
      }}>
        <BsCapsule color="#a8e6cf" /> MEDICINE INPUT
      </h3>

      {/* --- 2. Manual Input Section --- */}
      <form onSubmit={addMedicine} style={{ position: 'relative' }}>
          <input 
            type="text" 
            placeholder="Type medicine name..." 
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            style={{
                width: '100%',
                padding: '15px 50px 15px 15px', // Padding right for the button
                borderRadius: '10px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                color: 'white',
                outline: 'none',
                boxSizing: 'border-box'
            }}
          />
          <button 
            type="submit"
            style={{
                position: 'absolute', right: '5px', top: '5px', bottom: '5px',
                width: '40px',
                border: 'none', borderRadius: '8px',
                background: '#667eea', color: 'white',
                cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.2rem'
            }}
          >
              <BsPlus />
          </button>
      </form>

      {/* --- 3. The List --- */}
      <div style={{
          minHeight: '100px', maxHeight: '150px', overflowY: 'auto',
          display: 'flex', flexWrap: 'wrap', gap: '8px', alignContent: 'flex-start'
      }}>
          {medicines.length === 0 && (
              <div style={{ width: '100%', textAlign: 'center', color: '#555', fontSize: '0.9rem', marginTop: '20px' }}>
                  List is empty. Add medicines or browse file.
              </div>
          )}
          
          {medicines.map((med, index) => (
              <div key={index} style={{
                  background: 'rgba(168, 230, 207, 0.15)', // Light Green Tint
                  border: '1px solid rgba(168, 230, 207, 0.3)',
                  padding: '5px 10px',
                  borderRadius: '15px',
                  color: '#a8e6cf',
                  fontSize: '0.85rem',
                  display: 'flex', alignItems: 'center', gap: '5px'
              }}>
                  {med}
                  <BsX 
                    onClick={() => removeMedicine(index)} 
                    style={{ cursor: 'pointer', fontSize: '1.1rem' }}
                    onMouseEnter={(e) => e.target.style.color = 'white'}
                    onMouseLeave={(e) => e.target.style.color = '#a8e6cf'}
                  />
              </div>
          ))}
      </div>

      {/* --- 4. Submit Action --- */}
      <button 
        onClick={handleSubmit}
        disabled={medicines.length === 0 && !selectedFile}
        style={{
            padding: '12px',
            borderRadius: '10px',
            border: 'none',
            background: (medicines.length > 0 || selectedFile) 
                ? 'linear-gradient(135deg, #a8e6cf 0%, #3dc1d3 100%)' // Green/Blue Gradient
                : 'rgba(255,255,255,0.1)',
            color: (medicines.length > 0 || selectedFile) ? '#020204' : '#666',
            fontWeight: 'bold',
            cursor: (medicines.length > 0 || selectedFile) ? 'pointer' : 'not-allowed',
            transition: 'all 0.3s'
        }}
      >
        Analyze Dosage
      </button>

    </div>
  );
};

export default Browse_Medicine;