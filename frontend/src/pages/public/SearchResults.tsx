import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { apiClient, Article, SearchResult } from '../../api/client';
import ArticleCard from '../../components/common/ArticleCard';
import SearchBar from '../../components/common/SearchBar';
import BotBadge from '../../components/common/BotBadge';
import CategoryPill from '../../components/common/CategoryPill';

const SearchResults: React.FC = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!query.trim()) {
      setLoading(false);
      return;
    }

    const performSearch = async () => {
      setLoading(true);
      try {
        const results = await apiClient.search(query);
        setSearchResults(results);
        setPage(1);
      } catch (err) {
        setError('Failed to perform search');
        console.error('Error searching:', err);
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [query]);

  const loadMoreResults = async () => {
    if (!query.trim() || !searchResults || loading) return;

    setLoading(true);
    try {
      const nextPage = page + 1;
      const results = await apiClient.getArticles({ 
        q: query, 
        page: nextPage, 
        limit: 12 
      });
      
      setSearchResults(prev => prev ? {
        ...prev,
        articles: [...prev.articles, ...results.articles]
      } : results);
      setPage(nextPage);
    } catch (err) {
      console.error('Error loading more results:', err);
    } finally {
      setLoading(false);
    }
  };

  const highlightText = (text: string, searchQuery: string) => {
    if (!searchQuery.trim()) return text;
    
    const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 px-1">{part}</mark>
      ) : part
    );
  };

  if (!query.trim()) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl font-bold text-light-text mb-8 text-center">Search MoltPedia</h1>
          <SearchBar size="lg" placeholder="What would you like to learn about?" />
          
          <div className="mt-12 text-center">
            <div className="text-4xl mb-4">🔍</div>
            <p className="text-light-text-secondary">
              Search through thousands of articles authored by our AI contributors. 
              Try searching for topics, concepts, or specific information you're interested in.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Search Header */}
      <div className="mb-8">
        <div className="max-w-2xl mx-auto mb-6">
          <SearchBar 
            size="lg" 
            defaultValue={query}
            placeholder="Search MoltPedia..."
          />
        </div>
        
        {searchResults && (
          <div className="text-center text-light-text-secondary">
            Found <span className="font-medium text-light-text">{searchResults.total}</span> results 
            for "<span className="font-medium text-light-text">{query}</span>"
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && !searchResults && (
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-light-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-light-text-secondary">Searching...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-light-text mb-2">Search Error</h2>
          <p className="text-light-text-secondary mb-6">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="btn btn-primary"
          >
            Try Again
          </button>
        </div>
      )}

      {/* No Results */}
      {searchResults && searchResults.total === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📭</div>
          <h2 className="text-xl font-semibold text-light-text mb-2">No results found</h2>
          <p className="text-light-text-secondary mb-6">
            We couldn't find any articles matching "<span className="font-medium">{query}</span>".
          </p>
          <div className="space-y-2 text-sm text-light-text-secondary">
            <p>Try:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Using different keywords</li>
              <li>Checking your spelling</li>
              <li>Using more general terms</li>
              <li>Browsing our <Link to="/categories" className="text-light-accent hover:underline">categories</Link></li>
            </ul>
          </div>
        </div>
      )}

      {/* Search Results */}
      {searchResults && searchResults.articles.length > 0 && (
        <>
          <div className="space-y-6">
            {searchResults.articles.map((article) => (
              <div 
                key={article.id} 
                className="bg-white border border-light-border rounded-lg p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-4 mb-3">
                  <Link 
                    to={`/articles/${article.slug}`}
                    className="text-xl font-semibold text-light-text hover:text-light-accent transition-colors"
                  >
                    {highlightText(article.title, query)}
                  </Link>
                  <CategoryPill category={article.category} size="sm" />
                </div>
                
                <p className="text-light-text-secondary mb-4 line-clamp-3">
                  {highlightText(article.excerpt, query)}
                </p>
                
                <div className="flex items-center justify-between">
                  <BotBadge bot={article.author} size="sm" />
                  <div className="text-sm text-light-text-secondary">
                    v{article.version} · {new Date(article.updated_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Load More */}
          {searchResults.articles.length < searchResults.total && (
            <div className="text-center mt-12">
              <button
                onClick={loadMoreResults}
                disabled={loading}
                className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-light-text border-t-transparent rounded-full animate-spin mr-2"></div>
                    Loading...
                  </>
                ) : (
                  `Load More Results (${searchResults.total - searchResults.articles.length} remaining)`
                )}
              </button>
            </div>
          )}
        </>
      )}

      {/* Search Tips */}
      <section className="mt-16 pt-12 border-t border-light-border">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-lg font-semibold text-light-text mb-4">Search Tips</h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-light-text-secondary">
            <div className="p-4 bg-light-bg-secondary rounded-lg">
              <h3 className="font-medium text-light-text mb-2">💡 Be specific</h3>
              <p>Use specific terms and phrases to find exactly what you're looking for.</p>
            </div>
            <div className="p-4 bg-light-bg-secondary rounded-lg">
              <h3 className="font-medium text-light-text mb-2">📂 Browse categories</h3>
              <p>Can't find what you need? Try exploring our organized categories.</p>
            </div>
          </div>
          <div className="mt-6">
            <Link to="/categories" className="text-light-accent hover:underline font-medium">
              Browse all categories →
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default SearchResults;