import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CalendarView = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [days, setDays] = useState(1); // 1=today, 2=tomorrow, 7=this week

  const fetchEvents = async (daysParam) => {
    setLoading(true);
    try {
      const res = await axios.get(`http://localhost:8000/dashboard/calendar_events?days=${daysParam}`);
      if (res.data.success) {
        setEvents(res.data.events);
      } else {
        setError(res.data.message || 'Failed to fetch events');
      }
    } catch (err) {
      console.error(err);
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents(days);
  }, [days]);

  // Format date/time for display
  const formatDate = (dateStr) => {
    try {
      const dt = new Date(dateStr);
      return dt.toLocaleString('en-US', { 
        weekday: 'short', month: 'short', day: 'numeric', 
        hour: 'numeric', minute: '2-digit', hour12: true 
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) return <div className="card" style={{ marginTop: '20px' }}>🗓️ Loading calendar...</div>;
  if (error) return <div className="card" style={{ marginTop: '20px', color: '#f87171' }}>{error}</div>;

  return (
    <div className="card" style={{ marginTop: '20px' }}>
      <h3>🗓️ Your Schedule</h3>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
        <button 
          onClick={() => setDays(1)} 
          style={{ 
            padding: '8px 18px', 
            borderRadius: '30px', 
            border: 'none', 
            background: days === 1 ? '#6dd5ed' : '#2a3050', 
            color: days === 1 ? '#000' : '#eaeef2',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          Today
        </button>
        <button 
          onClick={() => setDays(2)} 
          style={{ 
            padding: '8px 18px', 
            borderRadius: '30px', 
            border: 'none', 
            background: days === 2 ? '#6dd5ed' : '#2a3050', 
            color: days === 2 ? '#000' : '#eaeef2',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          Tomorrow
        </button>
        <button 
          onClick={() => setDays(7)} 
          style={{ 
            padding: '8px 18px', 
            borderRadius: '30px', 
            border: 'none', 
            background: days === 7 ? '#6dd5ed' : '#2a3050', 
            color: days === 7 ? '#000' : '#eaeef2',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          This Week
        </button>
      </div>

      {events.length === 0 ? (
        <p>📭 No events for this period.</p>
      ) : (
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {events.map((event, idx) => (
            <div key={idx} style={{
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '12px',
              padding: '14px 18px',
              marginBottom: '12px',
              border: '1px solid rgba(255,255,255,0.05)',
            }}>
              <div style={{ fontWeight: '600', fontSize: '1.05rem' }}>
                {event.summary || 'Untitled Event'}
              </div>
              <div style={{ fontSize: '0.85rem', color: '#8892b0', marginTop: '4px' }}>
                {formatDate(event.start)} – {formatDate(event.end)}
              </div>
              {event.description && (
                <div style={{ fontSize: '0.95rem', color: '#c8d0e0', marginTop: '8px' }}>
                  {event.description}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CalendarView;