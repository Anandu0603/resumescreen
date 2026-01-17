import React from 'react';
import './templateStyles.js';

export default function TemplateLanding() {
  return (
    <div>
      {/* Example: Use Bootstrap template's hero section markup here. */}
      <section className="hero section dark-background" style={{ minHeight: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="container d-flex flex-column align-items-center">
          <h2 style={{ fontWeight: 700, color: '#fff', fontSize: 48 }}>PLAN. LAUNCH. GROW.</h2>
          <p style={{ color: '#fff', fontSize: 22 }}>We are team of talented designers making websites with Bootstrap</p>
          <div className="d-flex mt-4">
            <a href="#about" className="btn-get-started btn btn-primary">Get Started</a>
            <a href="https://www.youtube.com/watch?v=Y7f98aduVJ8" className="btn-watch-video btn btn-light ms-3">Watch Video</a>
          </div>
        </div>
      </section>
      {/* Add more sections/components as needed for About, Services, etc. */}
    </div>
  );
}
