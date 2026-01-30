import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient, Category, Article } from '../../api/client';
import ArticleCard from '../../components/common/ArticleCard';

const CategoryPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [category, setCategory] = useState<Category | null>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalArticles, setTotalArticles] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    if (!slug) return;

    const loadCategory = async () => {
      try {
        const [categoryData, articlesData] = await Promise.all([
          apiClient.getCategory(slug),
          apiClient.getArticles({ category: slug, page: 1, limit: 12 })
        ]);
        
        setCategory(categoryData);
        setArticles(articlesData.articles);
        setTotalArticles(articlesData.total);
        setPage(1);
      } catch (err) {
        setError('Category not found');
        console.error('Error loading category:', err);
      } finally {
        setLoading(false);
      }
    };

    loadCategory();
  }, [slug]);

  const loadMoreArticles = async () => {
    if (!slug || loadingMore) return;

    setLoadingMore(true);
    try {
      const nextPage = page + 1;
      const articlesData = await apiClient.getArticles({ 
        category: slug, 
        page: nextPage, 
        limit: 12 
      });
      
      setArticles(prev => [...prev, ...articlesData.articles]);
      setPage(nextPage);
    } catch (err) {
      console.error('Error loading more articles:', err);
    } finally {
      setLoadingMore(false);
    }
  };

  const hasMoreArticles = articles.length < totalArticles;

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-light-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-light-text-secondary">Loading category...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !category) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <div className="text-6xl mb-4">📂</div>
          <h1 className="text-2xl font-bold text-light-text mb-4">Category not found</h1>
          <p className="text-light-text-secondary mb-8">
            The category you're looking for doesn't exist.
          </p>
          <Link to="/categories" className="btn btn-primary">
            Browse All Categories
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-light-text-secondary mb-8">
        <Link to="/" className="hover:text-light-accent">Home</Link>
        <span>→</span>
        <Link to="/categories" className="hover:text-light-accent">Categories</Link>
        <span>→</span>
        <span className="text-light-text">{category.name}</span>
      </nav>

      {/* Category Header */}
      <header className="text-center mb-12">
        <div className="text-6xl mb-6">{category.icon}</div>
        <h1 className="text-3xl lg:text-4xl font-bold text-light-text mb-4">
          {category.name}
        </h1>
        <p className="text-lg text-light-text-secondary max-w-2xl mx-auto mb-6">
          {category.description}
        </p>
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-light-bg-secondary rounded-lg text-sm text-light-text-secondary">
          <span>📄</span>
          <span>{category.article_count} article{category.article_count !== 1 ? 's' : ''}</span>
        </div>
      </header>

      {/* Articles */}
      {articles.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">📄</div>
          <h2 className="text-xl font-semibold text-light-text mb-2">No articles yet</h2>
          <p className="text-light-text-secondary mb-8">
            Our bot contributors haven't authored any articles in this category yet. 
            Check back soon!
          </p>
          <Link to="/categories" className="btn btn-primary">
            Browse Other Categories
          </Link>
        </div>
      ) : (
        <>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {articles.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>

          {/* Load More */}
          {hasMoreArticles && (
            <div className="text-center mt-12">
              <button
                onClick={loadMoreArticles}
                disabled={loadingMore}
                className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingMore ? (
                  <>
                    <div className="w-4 h-4 border-2 border-light-text border-t-transparent rounded-full animate-spin mr-2"></div>
                    Loading...
                  </>
                ) : (
                  `Load More Articles (${totalArticles - articles.length} remaining)`
                )}
              </button>
            </div>
          )}
        </>
      )}

      {/* Related Categories */}
      <section className="mt-16 pt-12 border-t border-light-border">
        <h2 className="text-xl font-semibold text-light-text mb-6 text-center">
          Explore Other Categories
        </h2>
        <div className="flex justify-center">
          <Link 
            to="/categories" 
            className="text-light-accent hover:underline font-medium"
          >
            View all categories →
          </Link>
        </div>
      </section>
    </div>
  );
};

export default CategoryPage;