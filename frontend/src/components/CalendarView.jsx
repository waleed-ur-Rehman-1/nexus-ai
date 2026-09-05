import React, { useState, useEffect } from 'react';
import { getCalendarEvents } from '../services/api';

const CalendarView = ({ days = 1 }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const data = await getCalendarEvents(days);
        if (data.success) {
          setEvents(data.events);
        } else {
          setError(data.message || 'Failed to fetch events');
        }
      } catch (err) {
        console.error('Calendar fetch error:', err);
        setError('Network error');
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, [days]);

  // ... render
};

export default CalendarView;