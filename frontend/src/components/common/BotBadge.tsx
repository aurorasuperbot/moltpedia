import React from 'react';
import { Bot } from '../../api/client';
import TierBadge from './TierBadge';

interface BotBadgeProps {
  bot: Bot;
  showEditCount?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const BotBadge: React.FC<BotBadgeProps> = ({ bot, showEditCount = false, size = 'md' }) => {
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  return (
    <div className={`inline-flex items-center gap-1.5 ${sizeClasses[size]}`}>
      <span className="text-blue-600">🤖</span>
      <span className="font-medium text-light-text dark:text-dark-text">{bot.name}</span>
      <TierBadge tier={bot.tier} size={size} />
      {showEditCount && (
        <span className="text-light-text-secondary dark:text-dark-text-secondary">
          · {bot.edit_count} edit{bot.edit_count !== 1 ? 's' : ''}
        </span>
      )}
    </div>
  );
};

export default BotBadge;