/**
 * WatcherButton - Watch/Unwatch amendments for notifications
 *
 * Features:
 * - Toggle watch/unwatch
 * - Display watcher count
 * - Show watching status
 */

import React, { useState, useEffect } from 'react';
import './WatcherButton.css';

// Get API base URL from environment or default to /api (for proxy)
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const WatcherButton = ({ amendmentId }) => {
  const [isWatching, setIsWatching] = useState(false);
  const [watcherCount, setWatcherCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showWatchers, setShowWatchers] = useState(false);
  const [watchers, setWatchers] = useState([]);

  useEffect(() => {
    if (amendmentId) {
      checkWatchStatus();
      loadWatchers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [amendmentId]);

  const checkWatchStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_BASE_URL}/amendments/${amendmentId}/is-watching`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setIsWatching(data.is_watching);
      }
    } catch (error) {
      console.error('Error checking watch status:', error);
    }
  };

  const loadWatchers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_BASE_URL}/amendments/${amendmentId}/watchers`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setWatchers(data);
        setWatcherCount(data.length);
      }
    } catch (error) {
      console.error('Error loading watchers:', error);
    }
  };

  const toggleWatch = async () => {
    if (loading) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');

      if (isWatching) {
        // Unwatch
        const response = await fetch(
          `${API_BASE_URL}/amendments/${amendmentId}/watchers`,
          {
            method: 'DELETE',
            headers: { Authorization: `Bearer ${token}` }
          }
        );

        if (response.ok) {
          setIsWatching(false);
          await loadWatchers();
        }
      } else {
        // Watch
        const response = await fetch(
          `${API_BASE_URL}/amendments/${amendmentId}/watchers`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ watch_reason: 'Manual' })
          }
        );

        if (response.ok) {
          setIsWatching(true);
          await loadWatchers();
        }
      }
    } catch (error) {
      console.error('Error toggling watch:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="watcher-button-container">
      <button
        className={`watcher-button ${isWatching ? 'watching' : ''}`}
        onClick={toggleWatch}
        disabled={loading}
        title={isWatching ? 'Unwatch this amendment' : 'Watch this amendment for notifications'}
      >
        <span className="watcher-icon">
          {isWatching ? '🔔' : '🔕'}
        </span>
        <span className="watcher-text">
          {isWatching ? 'Watching' : 'Watch'}
        </span>
        <span
          className="watcher-count"
          onClick={(e) => {
            e.stopPropagation();
            setShowWatchers(!showWatchers);
          }}
          title={`${watcherCount} watcher${watcherCount !== 1 ? 's' : ''}`}
        >
          {watcherCount}
        </span>
      </button>

      {showWatchers && watcherCount > 0 && (
        <div className="watchers-dropdown">
          <div className="watchers-header">
            <span>Watchers ({watcherCount})</span>
            <button
              className="close-dropdown"
              onClick={() => setShowWatchers(false)}
            >
              ×
            </button>
          </div>
          <div className="watchers-list">
            {watchers.map(watcher => (
              <div key={watcher.watcher_id} className="watcher-item">
                <div className="watcher-avatar">
                  {watcher.employee_name ? watcher.employee_name.charAt(0).toUpperCase() : '?'}
                </div>
                <div className="watcher-info">
                  <div className="watcher-name">{watcher.employee_name || 'Unknown'}</div>
                  <div className="watcher-reason">{watcher.watch_reason}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default WatcherButton;
