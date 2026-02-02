/**
 * QAComments Component
 *
 * Threaded comment system for QA discussions.
 * Features:
 * - Threaded replies (nested comments)
 * - @mentions with autocomplete
 * - Emoji reactions
 * - Create, edit, delete comments
 */

import React, { useState, useEffect, useRef } from 'react';
import CommentReactions from './CommentReactions';
import './QAComments.css';

// Get API base URL from environment or default to /api (for proxy)
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const QAComments = ({ amendmentId, currentUser }) => {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newComment, setNewComment] = useState('');
  const [commentType, setCommentType] = useState('General');
  const [submitting, setSubmitting] = useState(false);
  const [editingCommentId, setEditingCommentId] = useState(null);
  const [editText, setEditText] = useState('');

  // Threading and reply state
  const [replyingToId, setReplyingToId] = useState(null);
  const [replyText, setReplyText] = useState('');

  // Mention autocomplete state
  const [showMentionSuggestions, setShowMentionSuggestions] = useState(false);
  const [mentionSuggestions, setMentionSuggestions] = useState([]);
  const [, setMentionQuery] = useState('');
  const [activeMentionField, setActiveMentionField] = useState(null); // 'new' | 'reply' | 'edit'
  const textareaRef = useRef(null);

  // Load comments
  useEffect(() => {
    loadComments();
    // Poll for new comments every 30 seconds
    const interval = setInterval(loadComments, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [amendmentId]);

  const loadComments = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/amendments/${amendmentId}/qa-comments`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to load comments');

      const data = await response.json();
      setComments(data.items || []);
      setLoading(false);
    } catch (err) {
      console.error('Error loading comments:', err);
      setError('Failed to load comments');
      setLoading(false);
    }
  };

  // Mention autocomplete functions
  const searchEmployees = async (query) => {
    if (!query || query.length < 1) {
      setShowMentionSuggestions(false);
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/employees/search?q=${encodeURIComponent(query)}&limit=10`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (response.ok) {
        const employees = await response.json();
        setMentionSuggestions(employees);
        setShowMentionSuggestions(employees.length > 0);
      }
    } catch (err) {
      console.error('Error searching employees:', err);
    }
  };

  const handleTextChange = (text, field) => {
    // Update the appropriate text field
    if (field === 'new') {
      setNewComment(text);
    } else if (field === 'reply') {
      setReplyText(text);
    } else if (field === 'edit') {
      setEditText(text);
    }

    // Detect @ mention
    const lastAtIndex = text.lastIndexOf('@');
    if (lastAtIndex !== -1) {
      const afterAt = text.slice(lastAtIndex + 1);
      // Check if we're still in a mention (no space after @)
      if (!afterAt.includes(' ') && afterAt.length > 0) {
        setMentionQuery(afterAt);
        setActiveMentionField(field);
        searchEmployees(afterAt);
      } else {
        setShowMentionSuggestions(false);
      }
    } else {
      setShowMentionSuggestions(false);
    }
  };

  const insertMention = (employee) => {
    let currentText = '';
    let updateFn = null;

    if (activeMentionField === 'new') {
      currentText = newComment;
      updateFn = setNewComment;
    } else if (activeMentionField === 'reply') {
      currentText = replyText;
      updateFn = setReplyText;
    } else if (activeMentionField === 'edit') {
      currentText = editText;
      updateFn = setEditText;
    }

    const lastAtIndex = currentText.lastIndexOf('@');
    const newText = currentText.slice(0, lastAtIndex) + `@${employee.employee_name} `;
    updateFn(newText);
    setShowMentionSuggestions(false);
    setActiveMentionField(null);
  };

  const handleSubmitComment = async (e, parentCommentId = null) => {
    e.preventDefault();

    const textToSubmit = parentCommentId ? replyText : newComment;
    if (!textToSubmit.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      let url = `${API_BASE_URL}/amendments/${amendmentId}/qa-comments`;
      if (parentCommentId) {
        url += `?parent_comment_id=${parentCommentId}`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          amendment_id: amendmentId,
          employee_id: currentUser.employee_id,
          comment_text: textToSubmit,
          comment_type: commentType,
        }),
      });

      if (!response.ok) throw new Error('Failed to create comment');

      // Reload all comments to get updated threading
      await loadComments();

      // Clear the appropriate text field
      if (parentCommentId) {
        setReplyText('');
        setReplyingToId(null);
      } else {
        setNewComment('');
        setCommentType('General');
      }
    } catch (err) {
      console.error('Error creating comment:', err);
      setError('Failed to create comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = (commentId) => {
    setReplyingToId(commentId);
    setReplyText('');
  };

  const cancelReply = () => {
    setReplyingToId(null);
    setReplyText('');
  };

  const handleEditComment = async (commentId) => {
    if (!editText.trim()) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/qa-comments/${commentId}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({
            comment_text: editText,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to update comment');

      const updatedComment = await response.json();
      setComments(
        comments.map((c) => (c.comment_id === commentId ? updatedComment : c))
      );
      setEditingCommentId(null);
      setEditText('');
    } catch (err) {
      console.error('Error updating comment:', err);
      setError('Failed to update comment');
    }
  };

  const handleDeleteComment = async (commentId) => {
    if (!window.confirm('Are you sure you want to delete this comment?')) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/qa-comments/${commentId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to delete comment');

      setComments(comments.filter((c) => c.comment_id !== commentId));
    } catch (err) {
      console.error('Error deleting comment:', err);
      setError('Failed to delete comment');
    }
  };

  const startEditComment = (comment) => {
    setEditingCommentId(comment.comment_id);
    setEditText(comment.comment_text);
  };

  const cancelEdit = () => {
    setEditingCommentId(null);
    setEditText('');
  };

  const formatRelativeTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  const getCommentTypeIcon = (type) => {
    const icons = {
      General: '💬',
      Issue: '⚠️',
      Resolution: '✅',
      Question: '❓',
    };
    return icons[type] || '💬';
  };

  // Build threaded comment structure
  const buildCommentTree = (comments) => {
    const commentMap = {};
    const rootComments = [];

    // First pass: create a map of all comments
    comments.forEach(comment => {
      commentMap[comment.comment_id] = { ...comment, replies: [] };
    });

    // Second pass: build the tree
    comments.forEach(comment => {
      if (comment.parent_comment_id) {
        // This is a reply, add it to parent's replies
        const parent = commentMap[comment.parent_comment_id];
        if (parent) {
          parent.replies.push(commentMap[comment.comment_id]);
        }
      } else {
        // This is a root comment
        rootComments.push(commentMap[comment.comment_id]);
      }
    });

    return rootComments;
  };

  // Recursive component for threaded comments
  const ThreadedComment = ({ comment, depth = 0 }) => {
    const isEditing = editingCommentId === comment.comment_id;
    const isReplying = replyingToId === comment.comment_id;

    return (
      <div
        className="qa-comment"
        style={{ marginLeft: `${depth * 30}px` }}
      >
        <div className="qa-comment-header">
          <div className="qa-comment-author">
            <span className="qa-comment-avatar">
              {comment.employee_name?.charAt(0) || '?'}
            </span>
            <span className="qa-comment-author-name">
              {comment.employee_name || 'Unknown'}
            </span>
            <span className="qa-comment-type">
              {getCommentTypeIcon(comment.comment_type)} {comment.comment_type}
            </span>
          </div>
          <div className="qa-comment-meta">
            <span className="qa-comment-time">
              {formatRelativeTime(comment.created_on)}
            </span>
            {comment.is_edited && (
              <span className="qa-comment-edited">(edited)</span>
            )}
            {comment.employee_id === currentUser?.employee_id && (
              <div className="qa-comment-actions">
                {!isEditing && (
                  <>
                    <button
                      onClick={() => startEditComment(comment)}
                      className="qa-comment-action-btn"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteComment(comment.comment_id)}
                      className="qa-comment-action-btn qa-comment-action-btn--danger"
                    >
                      Delete
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {isEditing ? (
          <div className="qa-comment-edit">
            <div className="mention-input-wrapper">
              <textarea
                value={editText}
                onChange={(e) => handleTextChange(e.target.value, 'edit')}
                className="qa-comment-textarea"
                rows="3"
              />
              {showMentionSuggestions && activeMentionField === 'edit' && (
                <MentionSuggestions
                  suggestions={mentionSuggestions}
                  onSelect={insertMention}
                />
              )}
            </div>
            <div className="qa-comment-edit-actions">
              <button
                onClick={() => handleEditComment(comment.comment_id)}
                className="qa-comment-submit-btn"
              >
                Save
              </button>
              <button
                onClick={cancelEdit}
                className="qa-comment-cancel-btn"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="qa-comment-text">{comment.comment_text}</div>

            {/* Reactions */}
            <CommentReactions
              commentId={comment.comment_id}
              initialReactions={comment.reaction_summary || {}}
            />

            {/* Reply button */}
            <div className="qa-comment-footer">
              <button
                onClick={() => handleReply(comment.comment_id)}
                className="qa-comment-reply-btn"
              >
                💬 Reply
              </button>
            </div>

            {/* Reply form */}
            {isReplying && (
              <div className="qa-reply-form">
                <div className="mention-input-wrapper">
                  <textarea
                    value={replyText}
                    onChange={(e) => handleTextChange(e.target.value, 'reply')}
                    placeholder="Write a reply... Use @ to mention someone"
                    className="qa-comment-textarea"
                    rows="2"
                    disabled={submitting}
                  />
                  {showMentionSuggestions && activeMentionField === 'reply' && (
                    <MentionSuggestions
                      suggestions={mentionSuggestions}
                      onSelect={insertMention}
                    />
                  )}
                </div>
                <div className="qa-reply-form-actions">
                  <button
                    onClick={(e) => handleSubmitComment(e, comment.comment_id)}
                    className="qa-comment-submit-btn"
                    disabled={submitting || !replyText.trim()}
                  >
                    {submitting ? 'Posting...' : 'Post Reply'}
                  </button>
                  <button
                    onClick={cancelReply}
                    className="qa-comment-cancel-btn"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Nested replies */}
        {comment.replies && comment.replies.length > 0 && (
          <div className="qa-comment-replies">
            {comment.replies.map(reply => (
              <ThreadedComment
                key={reply.comment_id}
                comment={reply}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  // Mention suggestions component
  const MentionSuggestions = ({ suggestions, onSelect }) => (
    <div className="mention-suggestions">
      {suggestions.map(emp => (
        <div
          key={emp.employee_id}
          onClick={() => onSelect(emp)}
          className="mention-suggestion-item"
        >
          <div className="mention-avatar">{emp.employee_name?.charAt(0) || '?'}</div>
          <div className="mention-info">
            <div className="mention-name">{emp.employee_name}</div>
            <div className="mention-username">@{emp.username || emp.employee_name}</div>
          </div>
        </div>
      ))}
    </div>
  );

  if (loading) {
    return <div className="qa-comments-loading">Loading comments...</div>;
  }

  const threadedComments = buildCommentTree(comments);

  return (
    <div className="qa-comments">
      <div className="qa-comments-header">
        <h3>QA Discussion ({comments.length})</h3>
      </div>

      {error && <div className="qa-comments-error">{error}</div>}

      {/* New Comment Form */}
      <form className="qa-comment-form" onSubmit={(e) => handleSubmitComment(e, null)}>
        <div className="qa-comment-form-header">
          <select
            value={commentType}
            onChange={(e) => setCommentType(e.target.value)}
            className="qa-comment-type-select"
          >
            <option value="General">💬 General</option>
            <option value="Issue">⚠️ Issue</option>
            <option value="Resolution">✅ Resolution</option>
            <option value="Question">❓ Question</option>
          </select>
        </div>
        <div className="mention-input-wrapper">
          <textarea
            ref={textareaRef}
            value={newComment}
            onChange={(e) => handleTextChange(e.target.value, 'new')}
            placeholder="Add a comment to the QA discussion... Use @ to mention someone"
            className="qa-comment-textarea"
            rows="3"
            disabled={submitting}
          />
          {showMentionSuggestions && activeMentionField === 'new' && (
            <MentionSuggestions
              suggestions={mentionSuggestions}
              onSelect={insertMention}
            />
          )}
        </div>
        <div className="qa-comment-form-actions">
          <button
            type="submit"
            className="qa-comment-submit-btn"
            disabled={submitting || !newComment.trim()}
          >
            {submitting ? 'Posting...' : 'Post Comment'}
          </button>
        </div>
      </form>

      {/* Threaded Comments List */}
      <div className="qa-comments-list">
        {threadedComments.length === 0 ? (
          <div className="qa-comments-empty">
            No comments yet. Start the discussion!
          </div>
        ) : (
          threadedComments.map((comment) => (
            <ThreadedComment
              key={comment.comment_id}
              comment={comment}
              depth={0}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default QAComments;
