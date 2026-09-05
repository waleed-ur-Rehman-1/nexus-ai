import React, { useState, useRef, useEffect } from 'react';
import { sendCommand, approveTask, rejectTask } from '../services/api';

const VoiceControl = ({ onCommandComplete }) => {
  const [isActive, setIsActive] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [result, setResult] = useState(null);
  const [approvalId, setApprovalId] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const recognitionRef = useRef(null);
  const commandTimeoutRef = useRef(null);

  // ---------- Speak ----------
  const speak = (text, callback) => {
    if (!window.speechSynthesis) {
      if (callback) callback();
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 0.9;
    utterance.pitch = 0.8;
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.name.includes('Google UK English Female')) ||
                      voices.find(v => v.lang.startsWith('en-GB')) ||
                      voices.find(v => v.lang.startsWith('en-US')) ||
                      voices[0];
    if (preferred) utterance.voice = preferred;
    utterance.onend = () => { if (callback) callback(); };
    utterance.onerror = () => { if (callback) callback(); };
    window.speechSynthesis.speak(utterance);
  };

  // ---------- Process command ----------
  const processCommand = async (commandText) => {
    setIsProcessing(true);
    setStatusMessage(`📝 Processing: "${commandText}"`);
    try {
      const data = await sendCommand(commandText);
      setResult(data);

      if (data.status === 'pending_approval') {
        const msg = `The command "${commandText}" requires approval. Risk level: ${data.approval.risk_level}. Do you approve?`;
        setApprovalId(data.approval.approval_id);
        setStatusMessage(`⚠️ ${msg}`);
        speak(msg);
        setIsProcessing(false);
        // Wait for user to click Approve/Reject
      } else if (data.status === 'completed') {
        const execResult = data.execution_result || {};
        let msg;
        if (execResult.success) {
          if (execResult.action === 'fetch_emails') {
            const count = execResult.count || 0;
            if (count === 0) msg = 'You have no new emails.';
            else {
              const subjects = execResult.emails.slice(0, 3).map(e => e.subject).join(', ');
              msg = count > 3 ? `You have ${count} emails: ${subjects}.` : `You have ${count} email(s): ${subjects}.`;
            }
          } else {
            msg = execResult.message || 'Task completed.';
          }
          setStatusMessage(`✅ ${msg}`);
          speak(msg, () => {
            setIsProcessing(false);
            // After speaking, go to command-listening (not wake) for a smooth follow-up
            startCommandListening();
          });
        } else {
          msg = execResult.message || 'Task failed.';
          setStatusMessage(`❌ ${msg}`);
          speak(`Task failed: ${msg}`, () => {
            setIsProcessing(false);
            startCommandListening();
          });
        }
        setApprovalId(null);
        if (onCommandComplete) onCommandComplete();
      } else {
        speak('Unexpected response.', () => {
          setIsProcessing(false);
          startCommandListening();
        });
      }
    } catch (err) {
      console.error(err);
      speak('Error sending command. Try again.', () => {
        setIsProcessing(false);
        startCommandListening();
      });
    }
  };

  // ---------- Command listening (direct, no wake word needed) ----------
  const startCommandListening = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
      recognitionRef.current = null;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setStatusMessage('❌ Speech recognition not supported.');
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onstart = () => setStatusMessage('🎤 Listening for command...');
    recognition.onresult = (event) => {
      const cmd = event.results[0][0].transcript.trim();
      setTranscript(cmd);
      if (cmd) processCommand(cmd);
      else startCommandListening();
    };
    recognition.onerror = (event) => {
      console.error('Command error:', event.error);
      if (event.error === 'not-allowed') {
        setStatusMessage('❌ Microphone access denied.');
        return;
      }
      // If error, go back to wake listening after a moment
      setTimeout(startWakeWordListening, 500);
    };
    recognition.onend = () => {
      // No speech detected – go back to wake listening after a short delay
      if (!isProcessing && isActive) {
        commandTimeoutRef.current = setTimeout(startWakeWordListening, 4000);
      }
    };
    recognitionRef.current = recognition;
    recognition.start();
  };

  // ---------- Wake word listener ----------
  const startWakeWordListening = () => {
    if (commandTimeoutRef.current) clearTimeout(commandTimeoutRef.current);
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
      recognitionRef.current = null;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setStatusMessage('❌ Speech recognition not supported.');
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onstart = () => setStatusMessage('🔊 Say "Hey Nexus" to wake me...');
    recognition.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript.toLowerCase().trim();
        if (transcript.includes('hey nexus') || transcript === 'nexus') {
          recognition.stop();
          setStatusMessage('🔊 Wake word detected!');
          speak('Yes?', () => {
            // After speaking, immediately start listening for command
            startCommandListening();
          });
          return;
        }
      }
    };
    recognition.onerror = (event) => {
      console.error('Wake error:', event.error);
      if (event.error === 'not-allowed') {
        setStatusMessage('❌ Microphone access denied.');
        setIsActive(false);
        return;
      }
      if (isActive) setTimeout(startWakeWordListening, 500);
    };
    recognition.onend = () => {
      if (isActive && !isProcessing) startWakeWordListening();
    };
    recognitionRef.current = recognition;
    recognition.start();
  };

  // ---------- Toggle ----------
  const toggleConversation = () => {
    if (isActive) {
      setIsActive(false);
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
        recognitionRef.current = null;
      }
      if (commandTimeoutRef.current) clearTimeout(commandTimeoutRef.current);
      window.speechSynthesis.cancel();
      setStatusMessage('⏹ Stopped.');
    } else {
      setIsActive(true);
      startWakeWordListening();
    }
  };

  // ---------- Approvals ----------
  const handleApprove = async () => {
    if (!approvalId) return;
    try {
      const res = await approveTask(approvalId);
      setResult(res);
      setApprovalId(null);
      const msg = 'Task approved and executed.';
      setStatusMessage(`✅ ${msg}`);
      speak(msg, () => startCommandListening());
      if (onCommandComplete) onCommandComplete();
    } catch (err) {
      console.error(err);
      speak('Approval failed.', () => startCommandListening());
    }
  };

  const handleReject = async () => {
    if (!approvalId) return;
    try {
      const res = await rejectTask(approvalId);
      setResult(res);
      setApprovalId(null);
      const msg = 'Task rejected.';
      setStatusMessage(`❌ ${msg}`);
      speak(msg, () => startCommandListening());
      if (onCommandComplete) onCommandComplete();
    } catch (err) {
      console.error(err);
      speak('Rejection failed.', () => startCommandListening());
    }
  };

  // ---------- Cleanup ----------
  useEffect(() => {
    return () => {
      if (recognitionRef.current) try { recognitionRef.current.stop(); } catch (e) {}
      if (commandTimeoutRef.current) clearTimeout(commandTimeoutRef.current);
      window.speechSynthesis.cancel();
    };
  }, []);

  return (
    <div className="card" style={{ animation: 'fadeUp 0.4s ease-out 0.2s both' }}>
      <h3>🎤 Voice Conversation</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
        <button
          onClick={toggleConversation}
          style={{
            background: isActive ? '#f87171' : '#6dd5ed',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '50px',
            fontWeight: '600',
            fontSize: '1rem',
            color: '#fff',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: isActive ? '0 0 30px rgba(248, 113, 113, 0.4)' : '0 0 30px rgba(109, 213, 237, 0.3)',
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          {isActive ? '⏹ Stop Conversation' : '🎙️ Start Conversation'}
        </button>
        {approvalId && (
          <>
            <button onClick={handleApprove} style={{ background: '#4ade80', border: 'none', padding: '10px 20px', borderRadius: '50px', fontWeight: '600', color: '#000', cursor: 'pointer' }}>✅ Approve</button>
            <button onClick={handleReject} style={{ background: '#f87171', border: 'none', padding: '10px 20px', borderRadius: '50px', fontWeight: '600', color: '#fff', cursor: 'pointer' }}>❌ Reject</button>
          </>
        )}
      </div>
      {statusMessage && <p style={{ marginTop: '12px', color: '#eaeef2' }}><strong>{statusMessage}</strong></p>}
      {transcript && <p style={{ marginTop: '8px', color: '#8892b0' }}><strong>You said:</strong> {transcript}</p>}
      {result && (
        <pre style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '12px', maxHeight: '200px', overflow: 'auto', fontSize: '0.85rem', marginTop: '12px' }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
};

export default VoiceControl;