import React, { useState, useRef } from 'react';
import { BsCloudUpload, BsImage, BsX, BsCheckCircle } from "react-icons/bs";

const Image_Uploader = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // Reference to the hidden file input
  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
    } else {
      alert("Please upload a valid image file.");
    }
  };

  const onInputChange = (e) => {
    handleFileSelect(e.target.files[0]);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const removeImage = (e) => {
    e.stopPropagation(); // Prevent triggering the click on parent
    setSelectedImage(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleUpload = () => {
    if (!selectedImage) return;
    console.log("Uploading:", selectedImage.name);
    alert(`Scanning ${selectedImage.name}... Analysis complete.`);
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
        alignItems: 'center',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        textAlign: 'center'
    }}>
      
      <h3 style={{ color: 'white', marginBottom: '20px', letterSpacing: '1px' }}>
        UPLOAD SCANS
      </h3>

      {/* --- Drag & Drop Zone --- */}
      <div 
        onClick={() => !previewUrl && fileInputRef.current.click()}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        style={{
            width: '100%',
            height: '250px',
            borderRadius: '15px',
            border: `2px dashed ${isDragging ? '#667eea' : 'rgba(255,255,255,0.2)'}`,
            backgroundColor: isDragging ? 'rgba(102, 126, 234, 0.1)' : 'rgba(0,0,0,0.2)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: previewUrl ? 'default' : 'pointer',
            transition: 'all 0.3s ease',
            position: 'relative',
            overflow: 'hidden'
        }}
      >
        <input 
            type="file" 
            ref={fileInputRef} 
            onChange={onInputChange} 
            accept="image/*" 
            style={{ display: 'none' }} 
        />

        {previewUrl ? (
            // --- Image Preview Mode ---
            <div style={{ position: 'relative', width: '100%', height: '100%' }}>
                <img 
                    src={previewUrl} 
                    alt="Preview" 
                    style={{ 
                        width: '100%', height: '100%', objectFit: 'cover', 
                        filter: 'brightness(0.9)'
                    }} 
                />
                
                {/* Remove Button */}
                <button 
                    onClick={removeImage}
                    style={{
                        position: 'absolute', top: '10px', right: '10px',
                        background: 'rgba(0,0,0,0.6)', color: 'white',
                        border: 'none', borderRadius: '50%',
                        width: '30px', height: '30px', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}
                >
                    <BsX size={20} />
                </button>

                {/* Simulated Scanning Line */}
                <div style={{
                    position: 'absolute', top: 0, left: 0,
                    width: '100%', height: '2px',
                    background: '#00d2d3',
                    boxShadow: '0 0 10px #00d2d3',
                    animation: 'scan 2s linear infinite'
                }}></div>
                <style>{`@keyframes scan { 0% {top: 0%} 50% {top: 100%} 100% {top: 0%} }`}</style>
            </div>
        ) : (
            // --- Empty State ---
            <>
                <BsCloudUpload size={40} color={isDragging ? '#667eea' : '#888'} style={{ marginBottom: '15px' }} />
                <p style={{ color: '#ccc', margin: '0', fontSize: '0.9rem' }}>
                    Drag & Drop or <span style={{ color: '#667eea', fontWeight: 'bold' }}>Browse</span>
                </p>
                <p style={{ color: '#666', fontSize: '0.8rem', marginTop: '5px' }}>
                    Supports: JPG, PNG, DICOM
                </p>
            </>
        )}
      </div>

      {/* --- Action Button --- */}
      <button 
        disabled={!selectedImage}
        onClick={handleUpload}
        style={{
            marginTop: '20px',
            padding: '12px 30px',
            borderRadius: '30px',
            border: 'none',
            width: '100%',
            background: !selectedImage 
                ? 'rgba(255,255,255,0.1)' 
                : 'linear-gradient(135deg, #00d2d3 0%, #0abde3 100%)', // Cyan Gradient
            color: !selectedImage ? '#666' : 'white',
            fontWeight: 'bold',
            cursor: !selectedImage ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s ease',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
            boxShadow: !selectedImage ? 'none' : '0 4px 15px rgba(10, 189, 227, 0.4)'
        }}
      >
        {selectedImage ? <><BsCheckCircle /> Analyze Image</> : "Select Image"}
      </button>

    </div>
  );
};

export default Image_Uploader;