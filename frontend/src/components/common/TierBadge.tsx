import React from 'react';
import { Bot } from '../../api/client';

interface TierBadgeProps {
  tier: Bot['tier'];
  size?: 'sm' | 'md' | 'lg';
}

const TierBadge: React.FC<TierBadgeProps> = ({ tier, size = 'md' }) => {
  const tierConfig = {
    admin: { icon: '🛡️', label: 'Admin', color: 'text-red-600' },
    founder: { icon: '🏛️', label: 'Founder', color: 'text-purple-600' },
    trusted: { icon: '⭐', label: 'Trusted', color: 'text-yellow-600' },
    new: { icon: '🆕', label: 'New', color: 'text-green-600' }
  };

  const config = tierConfig[tier];
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  return (
    <span className={`inline-flex items-center gap-1 ${config.color} ${sizeClasses[size]}`}>
      <span>{config.icon}</span>
      <span className="font-medium">{config.label}</span>
    </span>
  );
};

export default TierBadge;