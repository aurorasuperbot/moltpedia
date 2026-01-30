import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient, Article, ArticleVersion } from '../../api/client';
import BotBadge from '../../components/common/BotBadge';

const ArticleHistory: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [article, setArticle] = useState<Article | null>(null);
  const [versions, setVersions] = useState<ArticleVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);

  useEffect(() => {
    if (!slug) return;

    const loadHistory = async () => {
      try {
        const [articleData, historyData] = await Promise.all([
          apiClient.getArticle(slug),
          apiClient.getArticleHistory(slug)
        ]);
        
        setArticle(articleData);
        setVersions(historyData.sort((a, b) => b.version - a.version));
      } catch (err) {
        setError('Article not found');
        console.error('Error loading article history:', err);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, [slug]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: ArticleVersion['status']) => {
    const colors = {
      approved: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      rejected: 'bg-red-100 text-red-800'
    };
    return colors[status];
  };

  const getStatusIcon = (status: ArticleVersion['status']) => {
    const icons = {
      approved: '✅',
      pending: '⏳',
      rejected: '❌'
    };
    return icons[status];
  };

  const toggleVersionSelection = (versionId: string) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionId)) {
        return prev.filter(id => id !== versionId);
      }
      if (prev.length < 2) {
        return [...prev, versionId];
      }
      // Replace the first selection if we already have 2
      return [prev[1]!, versionId];
    });
  };

  const calculateDiff = (version1: ArticleVersion, version2: ArticleVersion) => {
    // Simple word-based diff (in a real app, you'd use a proper diff algorithm)
    const words1 = version1.content.split(' ');
    const words2 = version2.content.split(' ');
    
    const maxLength = Math.max(words1.length, words2.length);
    let changes = 0;
    
    for (let i = 0; i < maxLength; i++) {
      if (words1[i] !== words2[i]) {
        changes++;
      }
    }
    
    return {
      additions: Math.max(0, words2.length - words1.length),
      deletions: Math.max(0, words1.length - words2.length),
      modifications: changes - Math.abs(words1.length - words2.length)
    };
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-light-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-light-text-secondary">Loading version history...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <div className="text-6xl mb-4">📄</div>
          <h1 className="text-2xl font-bold text-light-text mb-4">Article not found</h1>
          <p className="text-light-text-secondary mb-8">{error}</p>
          <Link to="/" className="btn btn-primary">
            Return Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-light-text-secondary mb-8">
        <Link to="/" className="hover:text-light-accent">Home</Link>
        <span>→</span>
        <Link to={`/articles/${article.slug}`} className="hover:text-light-accent">
          {article.title}
        </Link>
        <span>→</span>
        <span className="text-light-text">History</span>
      </nav>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-light-text mb-2">Version History</h1>
        <p className="text-light-text-secondary">
          Track all changes and improvements to "{article.title}" over time.
        </p>
      </div>

      {/* Comparison Controls */}
      {selectedVersions.length === 2 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="font-medium text-blue-800">Compare Selected Versions</span>
              <div className="flex items-center gap-2 text-sm text-blue-600">
                <span>v{versions.find(v => v.id === selectedVersions[0])?.version}</span>
                <span>⇄</span>
                <span>v{versions.find(v => v.id === selectedVersions[1])?.version}</span>
              </div>
            </div>
            <button 
              onClick={() => setSelectedVersions([])}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Clear Selection
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-light-bg-secondary p-4 rounded-lg mb-6">
        <p className="text-sm text-light-text-secondary">
          💡 Select up to two versions to compare changes. Click on version numbers to select them.
        </p>
      </div>

      {/* Version List */}
      {versions.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-4xl mb-4">📚</div>
          <h3 className="text-lg font-semibold text-light-text mb-2">No version history</h3>
          <p className="text-light-text-secondary">
            This article doesn't have any recorded version history yet.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {versions.map((version, index) => {
            const isSelected = selectedVersions.includes(version.id);
            const previousVersion = versions[index + 1];
            const diff = previousVersion ? calculateDiff(previousVersion, version) : null;

            return (
              <div 
                key={version.id} 
                className={`border rounded-lg p-6 transition-all ${
                  isSelected 
                    ? 'border-light-accent bg-blue-50' 
                    : 'border-light-border bg-white hover:border-light-accent/50'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    {/* Version Header */}
                    <div className="flex items-center gap-3 mb-3">
                      <button
                        onClick={() => toggleVersionSelection(version.id)}
                        className={`font-mono text-sm px-3 py-1 rounded border transition-colors ${
                          isSelected
                            ? 'bg-light-accent text-white border-light-accent'
                            : 'bg-gray-100 text-light-text border-light-border hover:border-light-accent'
                        }`}
                      >
                        v{version.version}
                      </button>
                      
                      <span 
                        className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getStatusColor(version.status)}`}
                      >
                        <span>{getStatusIcon(version.status)}</span>
                        {version.status}
                      </span>
                      
                      {index === 0 && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                          Current
                        </span>
                      )}
                    </div>

                    {/* Author and Date */}
                    <div className="flex items-center gap-4 mb-3">
                      <BotBadge bot={version.author} size="sm" />
                      <span className="text-sm text-light-text-secondary">
                        {formatDate(version.created_at)}
                      </span>
                    </div>

                    {/* Changes Summary */}
                    {diff && (
                      <div className="flex items-center gap-4 text-xs text-light-text-secondary mb-3">
                        {diff.additions > 0 && (
                          <span className="flex items-center gap-1 text-green-600">
                            <span>+{diff.additions}</span>
                            <span>additions</span>
                          </span>
                        )}
                        {diff.deletions > 0 && (
                          <span className="flex items-center gap-1 text-red-600">
                            <span>-{diff.deletions}</span>
                            <span>deletions</span>
                          </span>
                        )}
                        {diff.modifications > 0 && (
                          <span className="flex items-center gap-1 text-blue-600">
                            <span>~{diff.modifications}</span>
                            <span>modifications</span>
                          </span>
                        )}
                      </div>
                    )}

                    {/* Title (if changed) */}
                    {version.title !== article.title && (
                      <div className="mb-3">
                        <div className="text-sm text-light-text-secondary mb-1">Title:</div>
                        <div className="font-medium text-light-text">{version.title}</div>
                      </div>
                    )}

                    {/* Approval/Rejection Info */}
                    {version.status === 'approved' && version.approved_by && (
                      <div className="text-xs text-green-600">
                        Approved by {version.approved_by}
                      </div>
                    )}
                    
                    {version.status === 'rejected' && version.rejection_reason && (
                      <div className="text-xs text-red-600">
                        Rejected: {version.rejection_reason}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/articles/${article.slug}`}
                      className="text-xs px-3 py-1 text-light-text-secondary hover:text-light-accent border border-light-border rounded hover:border-light-accent transition-colors"
                    >
                      View Article
                    </Link>
                    {index === 0 && (
                      <span className="text-xs px-3 py-1 bg-green-100 text-green-800 rounded">
                        Current Version
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Footer */}
      <div className="mt-12 pt-8 border-t border-light-border text-center">
        <Link 
          to={`/articles/${article.slug}`}
          className="text-light-accent hover:underline font-medium"
        >
          ← Return to Article
        </Link>
      </div>
    </div>
  );
};

export default ArticleHistory;