import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ---------- Text Commands ----------
export const sendCommand = async (command) => {
  const res = await axios.post(`${API_BASE}/agent/command`, { command });
  return res.data;
};

// ---------- Approvals ----------
export const approveTask = async (approvalId) => {
  const res = await axios.post(`${API_BASE}/approval/approve`, { approval_id: approvalId });
  return res.data;
};

export const rejectTask = async (approvalId) => {
  const res = await axios.post(`${API_BASE}/approval/reject`, { approval_id: approvalId });
  return res.data;
};

// ---------- Voice ----------
export const sendVoice = async (audioBlob) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'voice.webm');
  const res = await axios.post(`${API_BASE}/voice/command`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
};

export const sendVoiceApproval = async (audioBlob, approvalId) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'approval.webm');
  formData.append('approval_id', approvalId);
  const res = await axios.post(`${API_BASE}/voice/approve`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
};

// ---------- Dashboard ----------
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