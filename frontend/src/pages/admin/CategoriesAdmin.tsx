import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient, Category } from '../../api/client';

const CategoriesAdmin: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newCategory, setNewCategory] = useState({
    name: '',
    slug: '',
    description: '',
    icon: '📂'
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await apiClient.getCategories();
      setCategories(data);
    } catch (err) {
      setError('Failed to load categories');
      console.error('Error loading categories:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  };

  const handleNameChange = (name: string) => {
    setNewCategory(prev => ({
      ...prev,
      name,
      slug: generateSlug(name)
    }));
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategory.name.trim() || !newCategory.description.trim()) return;

    setCreating(true);
    try {
      const created = await apiClient.createCategory(newCategory);
      setCategories(prev => [...prev, created]);
      setNewCategory({ name: '', slug: '', description: '', icon: '📂' });
      setShowCreateForm(false);
    } catch (err) {
      setError('Failed to create category');
      console.error('Error creating category:', err);
    } finally {
      setCreating(false);
    }
  };

  const commonIcons = ['📂', '💻', '🔬', '🎨', '📚', '🌍', '⚡', '🚀', '🔧', '💡', '🏛️', '🎯', '🌟', '🔥'];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-dark-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-dark-text-secondary">Loading categories...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-text">Categories Management</h1>
          <p className="text-dark-text-secondary">
            Organize and manage content categories for the wiki
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="btn btn-primary"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Category
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-100 border border-red-200 rounded-lg p-4 text-red-800">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            {error}
          </div>
        </div>
      )}

      {/* Create Category Form */}
      {showCreateForm && (
        <div className="bg-dark-bg-secondary border border-dark-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-dark-text">Create New Category</h2>
            <button
              onClick={() => setShowCreateForm(false)}
              className="text-dark-text-secondary hover:text-dark-text"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleCreateCategory} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-dark-text mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={newCategory.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  className="w-full px-3 py-2 border border-dark-border rounded-lg bg-dark-bg text-dark-text focus:outline-none focus:ring-2 focus:ring-dark-accent focus:border-transparent"
                  placeholder="e.g., Technology"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-text mb-1">
                  Slug
                </label>
                <input
                  type="text"
                  value={newCategory.slug}
                  onChange={(e) => setNewCategory(prev => ({ ...prev, slug: e.target.value }))}
                  className="w-full px-3 py-2 border border-dark-border rounded-lg bg-dark-bg text-dark-text focus:outline-none focus:ring-2 focus:ring-dark-accent focus:border-transparent"
                  placeholder="technology"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-text mb-1">
                Description
              </label>
              <textarea
                value={newCategory.description}
                onChange={(e) => setNewCategory(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-dark-border rounded-lg bg-dark-bg text-dark-text focus:outline-none focus:ring-2 focus:ring-dark-accent focus:border-transparent"
                rows={3}
                placeholder="Brief description of what this category contains..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-text mb-2">
                Icon
              </label>
              <div className="flex flex-wrap gap-2">
                {commonIcons.map((icon) => (
                  <button
                    key={icon}
                    type="button"
                    onClick={() => setNewCategory(prev => ({ ...prev, icon }))}
                    className={`w-10 h-10 text-xl rounded-lg border transition-colors ${
                      newCategory.icon === icon
                        ? 'border-dark-accent bg-dark-accent/20'
                        : 'border-dark-border hover:border-dark-accent hover:bg-dark-border'
                    }`}
                  >
                    {icon}
                  </button>
                ))}
                <input
                  type="text"
                  value={newCategory.icon}
                  onChange={(e) => setNewCategory(prev => ({ ...prev, icon: e.target.value }))}
                  className="w-16 px-2 py-2 border border-dark-border rounded-lg bg-dark-bg text-dark-text text-center focus:outline-none focus:ring-2 focus:ring-dark-accent focus:border-transparent"
                  placeholder="🔥"
                />
              </div>
            </div>

            <div className="flex items-center gap-3 pt-4">
              <button
                type="submit"
                disabled={creating || !newCategory.name.trim() || !newCategory.description.trim()}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Creating...
                  </>
                ) : (
                  'Create Category'
                )}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Categories List */}
      {categories.length === 0 ? (
        <div className="text-center py-16 bg-dark-bg-secondary rounded-lg border border-dark-border">
          <div className="text-6xl mb-4">📂</div>
          <h3 className="text-xl font-semibold text-dark-text mb-2">No categories yet</h3>
          <p className="text-dark-text-secondary mb-6">
            Create your first category to help organize wiki content.
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="btn btn-primary"
          >
            Create First Category
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {categories.map((category) => (
            <div key={category.id} className="bg-dark-bg-secondary border border-dark-border rounded-lg p-6">
              <div className="flex items-start justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{category.icon}</span>
                  <div>
                    <h3 className="font-semibold text-dark-text">{category.name}</h3>
                    <div className="text-xs text-dark-text-secondary font-mono">/{category.slug}</div>
                  </div>
                </div>
                <Link
                  to={`/categories/${category.slug}`}
                  className="text-xs px-2 py-1 border border-dark-border rounded hover:bg-dark-border transition-colors text-dark-text-secondary hover:text-dark-text"
                >
                  View
                </Link>
              </div>
              
              <p className="text-sm text-dark-text-secondary mb-4 line-clamp-3">
                {category.description}
              </p>
              
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1 text-dark-text-secondary">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>{category.article_count} articles</span>
                </div>
                <button className="text-dark-text-secondary hover:text-dark-text">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Statistics */}
      {categories.length > 0 && (
        <div className="bg-dark-bg-secondary border border-dark-border rounded-lg p-6">
          <h3 className="font-semibold text-dark-text mb-4">Category Statistics</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-dark-text">{categories.length}</div>
              <div className="text-sm text-dark-text-secondary">Total Categories</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-text">
                {categories.reduce((sum, cat) => sum + cat.article_count, 0)}
              </div>
              <div className="text-sm text-dark-text-secondary">Total Articles</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-text">
                {categories.length > 0 ? Math.round(categories.reduce((sum, cat) => sum + cat.article_count, 0) / categories.length) : 0}
              </div>
              <div className="text-sm text-dark-text-secondary">Avg. per Category</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-text">
                {Math.max(...categories.map(cat => cat.article_count), 0)}
              </div>
              <div className="text-sm text-dark-text-secondary">Largest Category</div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-center pt-8 border-t border-dark-border">
        <Link
          to="/admin/dashboard"
          className="text-dark-accent hover:underline font-medium"
        >
          ← Back to Dashboard
        </Link>
      </div>
    </div>
  );
};

export default CategoriesAdmin;