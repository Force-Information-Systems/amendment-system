/**
 * QA Dashboard Debug Version
 * Shows detailed step-by-step loading process
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../pages/QADashboard.css';

// Get API base URL from environment or default to /api (for proxy)
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const QADashboardDebug = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState('initializing');
  const [logs, setLogs] = useState([]);
  const [data, setData] = useState({});
  const [error, setError] = useState(null);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[${timestamp}] ${message}`);
    setLogs(prev => [...prev, { timestamp, message, type }]);
  };

  useEffect(() => {
    addLog('Component mounted', 'success');
    debugLoad();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const debugLoad = async () => {
    try {
      // Step 1: Check token
      setStep('checking-auth');
      addLog('Checking authentication token...');

      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');

      if (!token) {
        addLog('❌ No authentication token found', 'error');
        setError('Not logged in. Please login at /login first.');
        setStep('error');
        return;
      }

      addLog('✓ Token found', 'success');
      if (user) {
        const userData = JSON.parse(user);
        addLog(`✓ User: ${userData.employee_name} (ID: ${userData.employee_id})`, 'success');
        setData(prev => ({ ...prev, user: userData }));
      }

      // Step 2: Test backend connectivity
      setStep('testing-backend');
      addLog('Testing backend connectivity...');

      const healthResponse = await fetch(`${API_BASE_URL}/docs`);
      if (!healthResponse.ok) {
        addLog('❌ Backend not responding', 'error');
        setError('Backend server not available. Is it running on port 8000?');
        setStep('error');
        return;
      }
      addLog('✓ Backend is accessible', 'success');

      // Step 3: Load amendments
      setStep('loading-amendments');
      addLog('Loading amendments...');

      const amendmentsRes = await fetch(`${API_BASE_URL}/amendments?limit=10`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      addLog(`Amendments response: ${amendmentsRes.status} ${amendmentsRes.statusText}`);

      if (!amendmentsRes.ok) {
        const errorText = await amendmentsRes.text();
        addLog(`❌ Amendments failed: ${errorText}`, 'error');
        setError(`Failed to load amendments: HTTP ${amendmentsRes.status}`);
        setStep('error');
        return;
      }

      const amendmentsData = await amendmentsRes.json();
      addLog(`✓ Loaded ${amendmentsData.items?.length || 0} amendments`, 'success');
      setData(prev => ({ ...prev, amendments: amendmentsData }));

      // Step 4: Load applications
      setStep('loading-applications');
      addLog('Loading applications...');

      const appsRes = await fetch(`${API_BASE_URL}/applications`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (appsRes.ok) {
        const appsData = await appsRes.json();
        addLog(`✓ Loaded ${appsData?.length || 0} applications`, 'success');
        setData(prev => ({ ...prev, applications: appsData }));
      } else {
        addLog(`⚠ Applications failed: ${appsRes.status}`, 'warning');
      }

      // Step 5: Load employees
      setStep('loading-employees');
      addLog('Loading employees...');

      const employeesRes = await fetch(`${API_BASE_URL}/employees`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (employeesRes.ok) {
        const employeesData = await employeesRes.json();
        addLog(`✓ Loaded ${employeesData?.length || 0} employees`, 'success');
        setData(prev => ({ ...prev, employees: employeesData }));
      } else {
        addLog(`⚠ Employees failed: ${employeesRes.status}`, 'warning');
      }

      // Step 6: Load versions
      setStep('loading-versions');
      addLog('Loading versions...');

      const versionsRes = await fetch(`${API_BASE_URL}/versions`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (versionsRes.ok) {
        const versionsData = await versionsRes.json();
        addLog(`✓ Loaded ${versionsData?.length || 0} versions`, 'success');
        setData(prev => ({ ...prev, versions: versionsData }));
      } else {
        addLog(`⚠ Versions failed: ${versionsRes.status}`, 'warning');
      }

      // Success!
      setStep('complete');
      addLog('✅ All data loaded successfully!', 'success');
      addLog('The real QA Dashboard should work. Check console for any differences.', 'success');

    } catch (err) {
      addLog(`❌ Exception: ${err.message}`, 'error');
      console.error('Debug load error:', err);
      setError(err.message);
      setStep('error');
    }
  };

  const getStepColor = (currentStep) => {
    if (step === 'error') return '#ef4444';
    if (step === 'complete') return '#10b981';
    return '#3b82f6';
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>QA Dashboard Debug Mode</h1>

      <div style={{
        padding: '15px',
        background: getStepColor(step),
        color: 'white',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <strong>Current Step:</strong> {step}
      </div>

      {error && (
        <div style={{
          padding: '15px',
          background: '#fee2e2',
          color: '#991b1b',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '2px solid #ef4444'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={() => navigate('/qa-dashboard')}
          style={{
            padding: '10px 20px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            marginRight: '10px'
          }}
        >
          Try Real Dashboard
        </button>
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: '10px 20px',
            background: '#6b7280',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Reload Debug
        </button>
      </div>

      <h2>Loading Log:</h2>
      <div style={{
        background: '#1f2937',
        color: '#fff',
        padding: '15px',
        borderRadius: '8px',
        maxHeight: '400px',
        overflow: 'auto'
      }}>
        {logs.map((log, i) => (
          <div
            key={i}
            style={{
              marginBottom: '5px',
              color: log.type === 'error' ? '#ef4444' :
                     log.type === 'success' ? '#10b981' :
                     log.type === 'warning' ? '#f59e0b' : '#fff'
            }}
          >
            [{log.timestamp}] {log.message}
          </div>
        ))}
      </div>

      {step === 'complete' && (
        <div style={{ marginTop: '20px' }}>
          <h2>Loaded Data Summary:</h2>
          <pre style={{
            background: '#f3f4f6',
            padding: '15px',
            borderRadius: '8px',
            overflow: 'auto'
          }}>
            {JSON.stringify({
              amendments: data.amendments?.items?.length || 0,
              applications: data.applications?.length || 0,
              employees: data.employees?.length || 0,
              versions: data.versions?.length || 0
            }, null, 2)}
          </pre>
        </div>
      )}

      <div style={{ marginTop: '20px', fontSize: '12px', color: '#6b7280' }}>
        <p>This debug page tests the exact same API calls as the real QA Dashboard.</p>
        <p>Open browser console (F12) for detailed logs.</p>
      </div>
    </div>
  );
};

export default QADashboardDebug;
