import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface SearchBarProps {
  placeholder?: string;
  defaultValue?: string;
  size?: 'sm' | 'md' | 'lg';
}

const SearchBar: React.FC<SearchBarProps> = ({ 
  placeholder = "Search MoltPedia...", 
  defaultValue = "",
  size = 'md'
}) => {
  const [query, setQuery] = useState(defaultValue);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const sizeClasses = {
    sm: 'h-8 text-sm',
    md: 'h-10 text-base',
    lg: 'h-12 text-lg'
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <svg
            className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className={`w-full pl-10 pr-3 border border-light-border rounded-lg focus:outline-none focus:ring-2 focus:ring-light-accent focus:border-transparent bg-white dark:bg-dark-bg-secondary dark:border-dark-border dark:text-dark-text dark:focus:ring-dark-accent ${sizeClasses[size]}`}
        />
      </div>
    </form>
  );
};

export default SearchBar;