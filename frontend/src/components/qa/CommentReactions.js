/**
 * CommentReactions - Emoji reactions for QA comments
 *
 * Features:
 * - Display reactions with counts
 * - Toggle reactions (add/remove)
 * - Emoji picker
 * - Supported emojis: 👍 👎 ❤️ 🎉 😄 🚀
 */

import React, { useState, useEffect } from 'react';
import './CommentReactions.css';

// Get API base URL from environment or default to /api (for proxy)
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const CommentReactions = ({ commentId, initialReactions = {} }) => {
  const [reactions, setReactions] = useState(initialReactions);
  const [showPicker, setShowPicker] = useState(false);
  const [userReactions, setUserReactions] = useState(new Set());
  const [loading, setLoading] = useState(false);

  const availableEmojis = ['👍', '👎', '❤️', '🎉', '😄', '🚀'];

  useEffect(() => {
    loadReactions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [commentId]);

  const loadReactions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_BASE_URL}/comments/${commentId}/reactions/summary`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setReactions(data.reactions || {});
      }

      // Load user's reactions
      const userReactionsResponse = await fetch(
        `${API_BASE_URL}/comments/${commentId}/reactions`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (userReactionsResponse.ok) {
        const userReactionsData = await userReactionsResponse.json();
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        const myReactions = userReactionsData
          .filter(r => r.employee_id === currentUser.employee_id)
          .map(r => r.emoji);
        setUserReactions(new Set(myReactions));
      }
    } catch (error) {
      console.error('Error loading reactions:', error);
    }
  };

  const toggleReaction = async (emoji) => {
    if (loading) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_BASE_URL}/comments/${commentId}/reactions?emoji=${encodeURIComponent(emoji)}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.ok) {
        await response.json();

        // Update reactions
        await loadReactions();
        setShowPicker(false);
      } else {
        console.error('Failed to toggle reaction');
      }
    } catch (error) {
      console.error('Error toggling reaction:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="comment-reactions">
      <div className="reactions-display">
        {Object.entries(reactions).map(([emoji, count]) => {
          const isUserReaction = userReactions.has(emoji);
          return (
            <button
              key={emoji}
              className={`reaction-button ${isUserReaction ? 'user-reacted' : ''}`}
              onClick={() => toggleReaction(emoji)}
              disabled={loading}
              title={isUserReaction ? 'Remove your reaction' : 'Add reaction'}
            >
              <span className="reaction-emoji">{emoji}</span>
              <span className="reaction-count">{count}</span>
            </button>
          );
        })}
      </div>

      <div className="add-reaction-container">
        <button
          className="add-reaction-btn"
          onClick={() => setShowPicker(!showPicker)}
          disabled={loading}
          title="Add reaction"
        >
          😊 +
        </button>

        {showPicker && (
          <div className="emoji-picker">
            <div className="emoji-picker-header">
              <span>Add reaction</span>
              <button
                className="close-picker"
                onClick={() => setShowPicker(false)}
              >
                ×
              </button>
            </div>
            <div className="emoji-options">
              {availableEmojis.map(emoji => {
                const isUserReaction = userReactions.has(emoji);
                return (
                  <button
                    key={emoji}
                    onClick={() => toggleReaction(emoji)}
                    className={`emoji-option ${isUserReaction ? 'selected' : ''}`}
                    disabled={loading}
                    title={isUserReaction ? `Remove ${emoji}` : `Add ${emoji}`}
                  >
                    {emoji}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CommentReactions;
