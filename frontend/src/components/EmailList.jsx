import React, { useState, useEffect } from 'react';
import axios from 'axios';

const EmailList = () => {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEmails = async () => {
      try {
        const res = await axios.get('http://localhost:8000/dashboard/emails');
        if (res.data.success) {
          setEmails(res.data.emails);
        } else {
          setError(res.data.message || 'Failed to fetch emails');
        }
      } catch (err) {
        console.error('Email fetch error:', err);
        setError(err.message || 'Network error');
      } finally {
        setLoading(false);
      }
    };
    fetchEmails();
  }, []);

  if (loading) return <div className="card" style={{ textAlign: 'center', animation: 'fadeUp 0.4s ease-out' }}>📬 Loading emails...</div>;
  if (error) return <div className="card" style={{ borderColor: '#f87171' }}>⚠️ {error}</div>;
  if (emails.length === 0) return <div className="card">📭 No emails found.</div>;

  return (
    <div className="card" style={{ animation: 'fadeUp 0.4s ease-out 0.3s both' }}>
      <h3>📬 Recent Emails</h3>
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {emails.map((email, idx) => (
          <div
            key={idx}
            style={{
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '12px',
              padding: '14px 18px',
              marginBottom: '12px',
              border: '1px solid rgba(255,255,255,0.05)',
              transition: 'all 0.2s ease',
              cursor: 'default',
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.08)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
          >
            <div style={{ fontWeight: '600', fontSize: '1.05rem' }}>{email.subject}</div>
            <div style={{ fontSize: '0.85rem', color: '#8892b0', marginTop: '4px' }}>
              From: {email.from} · {email.date}
            </div>
            <div style={{ fontSize: '0.95rem', color: '#c8d0e0', marginTop: '8px' }}>
              {email.body}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EmailList;