import React from 'react'
import Galaxy from '../Animations_js/Galaxy.jsx'; // Adjust based on your folder structure
import { CiCircleChevUp } from "react-icons/ci";

// 1. Accept the props we passed from App.jsx
function Landing_page({ isOpen, onEnter }) {
  
  return (
      <div 
        className={isOpen ? "slide-up" : ""}
        style={{ 
           position: 'fixed', 
           top: 0, 
           left: 0, 
           width: '100%', 
           height: '100vh', 
           zIndex: 10,
           display: 'flex', 
           justifyContent: 'center',
           alignItems: 'center',
           flexDirection: 'column',
           backgroundColor: 'black', 
           transition: 'transform 2s ease-in-out', 
           overflow: 'hidden' 
        }}
      >
        
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: -1 }}>
          <Galaxy />
        </div>
        
        <p style={{fontSize: "10rem", fontWeight: 'bold', fontFamily: 'Arial Black', margin: '0', color: 'white'}}> 
            G.A.N.G.U 
        </p>
        <p style={{fontSize: "2rem", color: 'white'}}>
            Welcomes You
        </p>
        
        <button 
            onClick={onEnter}
            style={{
                background:'transparent',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                fontSize: '4rem', 
                zIndex: 2 
            }}
        >
            <CiCircleChevUp />
        </button>
  
      </div>
    )
}

export default Landing_page