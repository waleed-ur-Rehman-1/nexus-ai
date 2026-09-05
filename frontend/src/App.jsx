import React, { useState, useEffect } from 'react';
import VoiceControl from './components/VoiceControl';
import Dashboard from './components/Dashboard';
import EmailList from './components/EmailList';
import CalendarView from './components/CalendarView';
import { getStats, getRecentTasks, getPendingApprovals } from './services/api';
import './App.css';

function App() {
  const [stats, setStats] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);

  // Define fetchDashboard FIRST – before any useEffect or render
  const fetchDashboard = async () => {
    try {
      const [statsData, tasksData, approvalsData] = await Promise.all([
        getStats(),
        getRecentTasks(),
        getPendingApprovals()
      ]);
      setStats(statsData);
      setTasks(tasksData);
      setApprovals(approvalsData);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Now use it – it's defined
  useEffect(() => {
    fetchDashboard();
  }, []); // no dependency needed because fetchDashboard is stable

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🧠 NEXUS AI</h1>
        <p className="subtitle">Your Intelligent Digital Agent</p>
      </header>
      <main className="app-main">
        <VoiceControl onCommandComplete={fetchDashboard} />
        {loading ? (
          <div className="loading-spinner">⏳ Loading...</div>
        ) : (
          <>
            <Dashboard stats={stats} tasks={tasks} approvals={approvals} />
            <EmailList />
            <CalendarView />
          </>
        )}
      </main>
      <footer className="app-footer">
        <p>© 2026 NEXUS AI · Built with ❤️</p>
      </footer>
    </div>
  );
}

export default App;