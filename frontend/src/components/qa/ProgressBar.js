/**
 * ProgressBar Component
 *
 * Reusable component for displaying progress with percentage and label.
 * Used for test execution progress and checklist completion.
 */

import React from 'react';
import './ProgressBar.css';

const ProgressBar = ({
  completed,
  total,
  label = '',
  showPercentage = true,
  showFraction = true,
  size = 'medium',
  color = 'blue',
  animated = false,
}) => {
  // Calculate percentage
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

  // Determine color based on percentage if not explicitly set
  let barColor = color;
  if (color === 'auto') {
    if (percentage === 100) {
      barColor = 'green';
    } else if (percentage >= 60) {
      barColor = 'blue';
    } else if (percentage >= 30) {
      barColor = 'yellow';
    } else {
      barColor = 'red';
    }
  }

  return (
    <div className={`progress-bar-container progress-bar-container--${size}`}>
      {label && (
        <div className="progress-bar-header">
          <span className="progress-bar-label">{label}</span>
          {showFraction && (
            <span className="progress-bar-fraction">
              {completed}/{total}
            </span>
          )}
          {showPercentage && (
            <span className="progress-bar-percentage">{percentage}%</span>
          )}
        </div>
      )}
      <div className={`progress-bar progress-bar--${size}`}>
        <div
          className={`progress-bar-fill progress-bar-fill--${barColor} ${
            animated ? 'progress-bar-fill--animated' : ''
          }`}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin="0"
          aria-valuemax="100"
        >
          {!label && showPercentage && percentage > 15 && (
            <span className="progress-bar-percentage-inner">{percentage}%</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProgressBar;
