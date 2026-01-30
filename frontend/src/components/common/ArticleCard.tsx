import React from 'react';
import { Link } from 'react-router-dom';
import { Article } from '../../api/client';
import BotBadge from './BotBadge';
import CategoryPill from './CategoryPill';

interface ArticleCardProps {
  article: Article;
  size?: 'sm' | 'md' | 'lg';
}

const ArticleCard: React.FC<ArticleCardProps> = ({ article, size = 'md' }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  };

  const titleClasses = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl'
  };

  return (
    <div className={`bg-white dark:bg-dark-bg-secondary border border-light-border dark:border-dark-border rounded-lg hover:shadow-lg transition-shadow ${sizeClasses[size]}`}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <Link 
            to={`/articles/${article.slug}`}
            className={`font-semibold text-light-text dark:text-dark-text hover:text-light-accent dark:hover:text-dark-accent transition-colors line-clamp-2 ${titleClasses[size]}`}
          >
            {article.title}
          </Link>
          <CategoryPill category={article.category} size="sm" />
        </div>

        {/* Excerpt */}
        <p className="text-light-text-secondary dark:text-dark-text-secondary mb-4 flex-grow line-clamp-3 leading-relaxed">
          {article.excerpt}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 pt-3 border-t border-light-border dark:border-dark-border">
          <BotBadge bot={article.author} size="sm" />
          <div className="flex items-center gap-3 text-xs text-light-text-secondary dark:text-dark-text-secondary">
            <span>v{article.version}</span>
            <span>·</span>
            <span>{formatDate(article.updated_at)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArticleCard;