/**
 * StatusBadge Component
 *
 * Reusable component for displaying QA status with visual indicators.
 * Supports different sizes and optional icons.
 */

import React from 'react';
import './StatusBadge.css';

const StatusBadge = ({
  status,
  showIcon = true,
  size = 'medium',
  type = 'qa_status' // qa_status, overall_result, execution_status
}) => {
  // Status configurations with icons and colors
  const statusConfig = {
    // QA Status
    'Not Started': { icon: '⏸️', color: 'gray', label: 'Not Started' },
    'Assigned': { icon: '📋', color: 'blue', label: 'Assigned' },
    'In Testing': { icon: '🧪', color: 'blue', label: 'In Testing' },
    'Blocked': { icon: '🚫', color: 'orange', label: 'Blocked' },
    'Passed': { icon: '✅', color: 'green', label: 'Passed' },
    'Failed': { icon: '❌', color: 'red', label: 'Failed' },

    // Overall Result
    'Passed with Issues': { icon: '⚠️', color: 'yellow', label: 'Passed with Issues' },

    // Execution Status
    'Not Run': { icon: '⏸️', color: 'gray', label: 'Not Run' },
    'Skipped': { icon: '⏭️', color: 'gray', label: 'Skipped' },
  };

  const config = statusConfig[status] || { icon: '❓', color: 'gray', label: status };

  return (
    <span className={`status-badge status-badge--${config.color} status-badge--${size}`}>
      {showIcon && <span className="status-badge__icon">{config.icon}</span>}
      <span className="status-badge__label">{config.label}</span>
    </span>
  );
};

export default StatusBadge;
