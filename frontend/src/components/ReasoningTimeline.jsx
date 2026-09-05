import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ReasoningTimeline = ({ taskId }) => {
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReasoning = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/tasks/${taskId}/reasoning`);
        setSteps(res.data);
      } catch (err) {
        setError('Failed to load reasoning.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (taskId) fetchReasoning();
  }, [taskId]);

  if (loading) return <p style={{ color: '#8892b0', fontSize: '0.9rem' }}>🧠 Loading reasoning...</p>;
  if (error) return <p style={{ color: '#f87171' }}>{error}</p>;
  if (steps.length === 0) return <p style={{ color: '#8892b0' }}>No reasoning steps available.</p>;

  return (
    <div style={{ marginTop: '8px', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
      <h4 style={{ marginBottom: '8px', color: '#6dd5ed' }}>🧠 Reasoning</h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {steps.map((step, idx) => (
          <div key={idx} style={{ display: 'flex', alignItems: 'baseline', gap: '10px', fontSize: '0.9rem' }}>
            <span style={{ color: '#6dd5ed', minWidth: '60px', fontWeight: '500' }}>
              Step {step.step_order + 1}
            </span>
            <span style={{ color: '#eaeef2', fontWeight: '600' }}>{step.action}</span>
            <span style={{ color: '#8892b0', fontStyle: 'italic' }}>— {step.reason}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ReasoningTimeline;