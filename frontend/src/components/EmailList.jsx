import React, { useState, useEffect } from 'react';
import { getEmails } from '../services/api';

const EmailList = () => {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEmails = async () => {
      try {
        const data = await getEmails();  // uses environment variable
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

  // ... rest of your component (render logic)
};

export default EmailList;