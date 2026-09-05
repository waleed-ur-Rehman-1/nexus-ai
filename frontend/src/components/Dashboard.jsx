import React, { useState } from 'react';
import ReasoningTimeline from './ReasoningTimeline';

const Dashboard = ({ stats, tasks, approvals }) => {
  const [expandedTaskId, setExpandedTaskId] = useState(null);

  if (!stats) return null;

  const statItems = [
    { label: 'Total Tasks', value: stats.total, icon: '📋', color: '#6dd5ed' },
    { label: 'Completed', value: stats.completed, icon: '✅', color: '#4ade80' },
    { label: 'Pending', value: stats.pending, icon: '⏳', color: '#facc15' },
    { label: 'Approval Required', value: stats.pending_approval, icon: '⚠️', color: '#f87171' },
    { label: 'Failed', value: stats.failed, icon: '❌', color: '#f87171' },
  ];

  return (
    <div className="card" style={{ animation: 'fadeUp 0.4s ease-out' }}>
      <h2>📊 Dashboard Statistics</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '16px' }}>
        {statItems.map((item, idx) => (
          <div
            key={idx}
            style={{
              background: 'rgba(255,255,255,0.05)',
              padding: '1rem',
              borderRadius: '16px',
              textAlign: 'center',
              border: `1px solid ${item.color}33`,
              transition: 'all 0.3s ease',
              cursor: 'default',
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <div style={{ fontSize: '2rem' }}>{item.icon}</div>
            <div style={{ fontSize: '2rem', fontWeight: '700', color: item.color }}>{item.value}</div>
            <div style={{ fontSize: '0.85rem', color: '#8892b0' }}>{item.label}</div>
          </div>
        ))}
      </div>

      <h3 style={{ marginTop: '2rem' }}>📋 Recent Tasks</h3>
      {tasks.length === 0 ? (
        <p style={{ color: '#8892b0' }}>No tasks yet.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #2a3050' }}>
              <th style={{ textAlign: 'left', padding: '8px 0' }}>Command</th>
              <th style={{ textAlign: 'left', padding: '8px 0' }}>Agent</th>
              <th style={{ textAlign: 'left', padding: '8px 0' }}>Status</th>
              <th style={{ textAlign: 'left', padding: '8px 0' }}>Created</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(task => (
              <React.Fragment key={task.id}>
                <tr
                  onClick={() => setExpandedTaskId(expandedTaskId === task.id ? null : task.id)}
                  style={{ cursor: 'pointer', transition: 'background 0.2s' }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '8px 0' }}>{task.command}</td>
                  <td style={{ padding: '8px 0' }}>{task.agent}</td>
                  <td style={{ padding: '8px 0' }}>
                    <span style={{
                      background: task.status === 'completed' ? '#4ade8033' : task.status === 'failed' ? '#f8717133' : '#facc1533',
                      color: task.status === 'completed' ? '#4ade80' : task.status === 'failed' ? '#f87171' : '#facc15',
                      padding: '3px 12px',
                      borderRadius: '20px',
                      fontSize: '0.8rem',
                      fontWeight: '600'
                    }}>
                      {task.status}
                    </span>
                  </td>
                  <td style={{ padding: '8px 0', color: '#8892b0' }}>{new Date(task.created_at).toLocaleString()}</td>
                </tr>
                {expandedTaskId === task.id && (
                  <tr>
                    <td colSpan="4">
                      <ReasoningTimeline taskId={task.id} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      )}

      <h3 style={{ marginTop: '2rem' }}>🟡 Pending Approvals</h3>
      {approvals.length === 0 ? (
        <p style={{ color: '#8892b0' }}>No pending approvals.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {approvals.map(ap => (
            <li key={ap.id} style={{ padding: '10px 0', borderBottom: '1px solid #1f2540' }}>
              <div><strong>Action:</strong> {ap.action}</div>
              <div><span style={{ color: '#f87171' }}>Risk: {ap.risk_level}</span> · {new Date(ap.created_at).toLocaleString()}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Dashboard;