import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import TemplateLanding from './TemplateLanding';
import Home from './Home';
import About from './About';
import Services from './Services';
import Contact from './Contact';
import Login from './Login';
import Register from './Register';

// A wrapper component to handle protected routes
const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    // Redirect to /login, but save the current location they were trying to go to
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// Main App component with routing
const AppContent = () => {
  const [resume, setResume] = useState(null);
  const [jobDesc, setJobDesc] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const { user, logout } = useAuth();

  const handleFileChange = (e) => {
    setResume(e.target.files[0]);
  };

  const handleJobDescChange = (e) => {
    setJobDesc(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!resume || !jobDesc) return;
    setLoading(true);
    
    const formData = new FormData();
    formData.append('resume', resume);
    formData.append('job_description', jobDesc);
    
    try {
      const res = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include', // Include cookies for session
      });
      
      if (res.status === 401) {
        // Handle unauthorized (not logged in)
        window.location.href = '/login';
        return;
      }
      
      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error('Upload error:', error);
      setResult({ error: 'Failed to process resume. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleKeywordChange = (e) => setKeyword(e.target.value);

  const handleKeywordSearch = async (e) => {
    e.preventDefault();
    if (!keyword) return;
    setSearchLoading(true);
    setSearchResults([]);
    
    try {
      const res = await fetch(`http://localhost:5000/api/search?keyword=${encodeURIComponent(keyword)}`, {
        credentials: 'include', // Include cookies for session
      });
      
      if (res.status === 401) {
        // Handle unauthorized (not logged in)
        window.location.href = '/login';
        return;
      }
      
      const data = await res.json();
      setSearchResults(data.matches || []);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <>
      <header className="header">
        <div className="logo">📝 ResumeScreen.AI</div>
        <nav className="tabs">
          <button className={activeTab === 'home' ? 'active' : ''} onClick={() => setActiveTab('home')}>Home</button>
          <button className={activeTab === 'about' ? 'active' : ''} onClick={() => setActiveTab('about')}>About</button>
          <button className={activeTab === 'services' ? 'active' : ''} onClick={() => setActiveTab('services')}>Services</button>
          <button className={activeTab === 'contact' ? 'active' : ''} onClick={() => setActiveTab('contact')}>Contact</button>
          <button className={activeTab === 'screen' ? 'active' : ''} onClick={() => setActiveTab('screen')}>
            <span role="img" aria-label="screen">📄</span> Screen Resume
          </button>
          <button className={activeTab === 'search' ? 'active' : ''} onClick={() => setActiveTab('search')}>
            <span role="img" aria-label="search">🔍</span> Search Resumes
          </button>
          <button className={activeTab === 'landing' ? 'active' : ''} onClick={() => setActiveTab('landing')}>
            <span role="img" aria-label="landing">🌐</span> Landing Page
          </button>
        </nav>
      </header>
      {activeTab === 'landing' ? (
        <TemplateLanding />
      ) : (
        <>
          <div className="app-container">
            {activeTab === 'home' && <Home />}
            {activeTab === 'about' && <About />}
            {activeTab === 'services' && <Services />}
            {activeTab === 'contact' && <Contact />}
            {activeTab === 'screen' && (
              <>
                <h2>Screen Resume</h2>
                <form onSubmit={handleSubmit}>
                  <div>
                    <label>Upload Resume (PDF/DOCX): </label>
                    <input type="file" accept=".pdf,.docx" onChange={handleFileChange} />
                  </div>
                  <div style={{ marginTop: 16 }}>
                    <label>Paste Job Description:</label>
                    <textarea value={jobDesc} onChange={handleJobDescChange} rows={6} />
                  </div>
                  <button type="submit" disabled={loading}>
                    {loading ? 'Processing...' : 'Screen Resume'}
                  </button>
                </form>
                {result && (
                  <div className="result-card">
                    <h3>Results</h3>
                    <div className="score"><span role="img" aria-label="score">⭐</span> <b>Match Score:</b> {result.match_score || 'N/A'}%</div>
                    <div className="extract">
                      <b>Resume Extract:</b>
                      <pre>{result.resume_data?.raw_text || ''}</pre>
                    </div>
                    <div className="details">
                      <b>Details:</b> <pre>{JSON.stringify(result.details, null, 2)}</pre>
                    </div>
                  </div>
                )}
                {searchResults.length > 0 && (
                  <div className="search-results">
                    <h3>Search Results</h3>
                    <ul>
                      {searchResults.map((res, idx) => (
                        <li key={idx} className="resume-card">
                          <div><span role="img" aria-label="file">📄</span> <b>File:</b> {res.filename}</div>
                          <div><b>Extract:</b> <pre style={{ margin: 0 }}>{res.extract}</pre></div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {searchResults.length === 0 && keyword && !searchLoading && (
                  <div style={{ marginTop: 20, color: '#888' }}>No results found.</div>
                )}
              </>
            )}
          </div>
          <footer className="footer">
            <span> 2023 ResumeScreen.AI &middot; Made for College Project</span>
          </footer>
        </>
      )}
    </>
  );
}

export default App;
