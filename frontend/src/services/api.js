import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const sendCommand = async (command) => {
  const res = await axios.post(`${API_BASE}/agent/command`, { command });
  return res.data;
};

export const approveTask = async (approvalId) => {
  const res = await axios.post(`${API_BASE}/approval/approve`, { approval_id: approvalId });
  return res.data;
};

export const rejectTask = async (approvalId) => {
  const res = await axios.post(`${API_BASE}/approval/reject`, { approval_id: approvalId });
  return res.data;
};

export const getStats = async () => {
  const res = await axios.get(`${API_BASE}/dashboard/stats`);
  return res.data;
};

export const getRecentTasks = async (limit = 10) => {
  const res = await axios.get(`${API_BASE}/dashboard/recent_tasks`, { params: { limit } });
  return res.data;
};

export const getPendingApprovals = async () => {
  const res = await axios.get(`${API_BASE}/dashboard/pending_approvals`);
  return res.data;
};

export const getEmails = async (limit = 5) => {
  const res = await axios.get(`${API_BASE}/dashboard/emails`, { params: { limit } });
  return res.data;
};

export const getCalendarEvents = async (days = 1) => {
  const res = await axios.get(`${API_BASE}/dashboard/calendar_events`, { params: { days } });
  return res.data;
};