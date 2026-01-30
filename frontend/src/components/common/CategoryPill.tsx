import React from 'react';
import { Link } from 'react-router-dom';
import { Category } from '../../api/client';

interface CategoryPillProps {
  category: Category;
  size?: 'sm' | 'md';
}

const CategoryPill: React.FC<CategoryPillProps> = ({ category, size = 'md' }) => {
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm'
  };

  // Generate a consistent color based on category name
  const getColor = (name: string) => {
    const colors = [
      'bg-blue-100 text-blue-800 hover:bg-blue-200',
      'bg-green-100 text-green-800 hover:bg-green-200',
      'bg-purple-100 text-purple-800 hover:bg-purple-200',
      'bg-orange-100 text-orange-800 hover:bg-orange-200',
      'bg-pink-100 text-pink-800 hover:bg-pink-200',
      'bg-indigo-100 text-indigo-800 hover:bg-indigo-200'
    ];
    const hash = name.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return colors[Math.abs(hash) % colors.length];
  };

  const colorClass = getColor(category.name);

  return (
    <Link
      to={`/categories/${category.slug}`}
      className={`inline-flex items-center gap-1 rounded-full font-medium transition-colors ${colorClass} ${sizeClasses[size]}`}
    >
      <span>{category.icon}</span>
      {category.name}
    </Link>
  );
};

export default CategoryPill;