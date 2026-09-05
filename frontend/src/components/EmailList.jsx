import React, { useState, useEffect } from 'react';
import { getEmails } from '../services/api';

const EmailList = () => {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEmails = async () => {
      try {
        const data = await getEmails();
        if (data.success) {
          setEmails(data.emails);
        } else {
          setError(data.message || 'Failed to fetch emails');
        }
      } catch (err) {
        console.error('Email fetch error:', err);
        setError('Network error');
      } finally {
        setLoading(false);
      }
    };
    fetchEmails();
  }, []);

  if (loading) return <p>📬 Loading emails...</p>;
  if (error) return <p style={{ color: '#f87171' }}>{error}</p>;
  if (emails.length === 0) return <p>📭 No emails found.</p>;

  return (
    <div className="card" style={{ marginTop: '20px' }}>
      <h3>📬 Recent Emails</h3>
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {emails.map((email, idx) => (
          <div key={idx} style={{
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '12px',
            padding: '14px 18px',
            marginBottom: '12px',
            border: '1px solid rgba(255,255,255,0.05)',
          }}>
            <div style={{ fontWeight: '600' }}>{email.subject}</div>
            <div style={{ fontSize: '0.85rem', color: '#8892b0' }}>
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