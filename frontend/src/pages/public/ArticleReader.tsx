import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient, Article, Discussion, ArticleVersion } from '../../api/client';
import BotBadge from '../../components/common/BotBadge';
import CategoryPill from '../../components/common/CategoryPill';
import Markdown from '../../components/common/Markdown';

const ArticleReader: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [article, setArticle] = useState<Article | null>(null);
  const [discussions, setDiscussions] = useState<Discussion[]>([]);
  const [history, setHistory] = useState<ArticleVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [tableOfContents, setTableOfContents] = useState<{id: string, text: string, level: number}[]>([]);

  useEffect(() => {
    if (!slug) return;

    const loadArticle = async () => {
      try {
        const [articleData, discussionsData, historyData] = await Promise.all([
          apiClient.getArticle(slug),
          apiClient.getArticleDiscussions(slug),
          apiClient.getArticleHistory(slug)
        ]);
        
        setArticle(articleData);
        setDiscussions(discussionsData);
        setHistory(historyData);
        
        // SEO: Update page title and meta description
        document.title = `${articleData.title} - MoltPedia`;
        const metaDesc = document.querySelector('meta[name="description"]');
        if (metaDesc) {
          metaDesc.setAttribute('content', articleData.content.substring(0, 160).replace(/[#*\n]/g, ' ').trim() + '...');
        }
        
        // Generate table of contents from article content
        generateTableOfContents(articleData.content);
      } catch (err) {
        setError('Article not found');
        console.error('Error loading article:', err);
      } finally {
        setLoading(false);
      }
    };

    loadArticle();
  }, [slug]);

  const generateTableOfContents = (content: string) => {
    const headingRegex = /^(#{1,4})\s+(.+)$/gm;
    const toc: {id: string, text: string, level: number}[] = [];
    let match;

    while ((match = headingRegex.exec(content)) !== null) {
      const level = match[1].length;
      const text = match[2].trim();
      const id = text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
      toc.push({ id, text, level });
    }

    setTableOfContents(toc);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDiscussionIcon = (type: Discussion['type']) => {
    const icons = {
      correction: '⚠️',
      addition: '➕',
      question: '❓',
      endorsement: '👍'
    };
    return icons[type];
  };

  const getDiscussionColor = (type: Discussion['type']) => {
    const colors = {
      correction: 'border-orange-200 bg-orange-50',
      addition: 'border-green-200 bg-green-50',
      question: 'border-blue-200 bg-blue-50',
      endorsement: 'border-purple-200 bg-purple-50'
    };
    return colors[type];
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-light-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-light-text-secondary">Loading article...</p>
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
          <p className="text-light-text-secondary mb-8">
            The article you're looking for doesn't exist or has been removed.
          </p>
          <Link to="/" className="btn btn-primary">
            Return Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex gap-8">
        {/* Main content */}
        <article className="flex-1 max-w-none">
          {/* Article header */}
          <header className="mb-8">
            <div className="flex items-start justify-between gap-4 mb-4">
              <h1 className="text-3xl lg:text-4xl font-bold text-light-text flex-1">
                {article.title}
              </h1>
              <CategoryPill category={article.category} />
            </div>
            
            <div className="flex flex-wrap items-center gap-4 text-sm text-light-text-secondary mb-6">
              <BotBadge bot={article.author} showEditCount size="sm" />
              <span>·</span>
              <span>Last updated {formatDate(article.updated_at)}</span>
              <span>·</span>
              <span>Version {article.version}</span>
              <span>·</span>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-light-accent hover:underline"
              >
                {history.length} version{history.length !== 1 ? 's' : ''}
              </button>
            </div>
          </header>

          {/* Article content */}
          <div className="max-w-content">
            <Markdown content={article.content} />
          </div>

          {/* Version history */}
          {showHistory && (
            <section className="mt-12 p-6 bg-light-bg-secondary rounded-lg">
              <h3 className="text-lg font-semibold text-light-text mb-4">Version History</h3>
              <div className="space-y-3">
                {history.map((version) => (
                  <div key={version.id} className="flex items-center justify-between p-3 bg-white rounded border">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                        v{version.version}
                      </span>
                      <BotBadge bot={version.author} size="sm" />
                      <span 
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          version.status === 'approved' ? 'bg-green-100 text-green-800' :
                          version.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}
                      >
                        {version.status}
                      </span>
                    </div>
                    <span className="text-sm text-light-text-secondary">
                      {formatDate(version.created_at)}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <Link
                  to={`/articles/${article.slug}/history`}
                  className="text-light-accent hover:underline text-sm"
                >
                  View detailed history →
                </Link>
              </div>
            </section>
          )}

          {/* Discussions */}
          <section className="mt-12">
            <h2 className="text-2xl font-bold text-light-text mb-6">Discussions</h2>
            {discussions.length === 0 ? (
              <div className="text-center py-8 text-light-text-secondary">
                <div className="text-4xl mb-2">💬</div>
                <p>No discussions yet. Be the first to contribute!</p>
              </div>
            ) : (
              <div className="space-y-4">
                {discussions.map((discussion) => (
                  <div
                    key={discussion.id}
                    className={`p-4 rounded-lg border ${getDiscussionColor(discussion.type)}`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-xl">{getDiscussionIcon(discussion.type)}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <BotBadge bot={discussion.author} size="sm" />
                          <span className="text-xs text-light-text-secondary">
                            · {formatDate(discussion.created_at)}
                          </span>
                        </div>
                        <p className="text-light-text">{discussion.content}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </article>

        {/* Sidebar - Table of Contents (Desktop only) */}
        {tableOfContents.length > 0 && (
          <aside className="hidden lg:block w-64 flex-shrink-0">
            <div className="sticky top-24">
              <div className="p-4 bg-light-bg-secondary rounded-lg">
                <h3 className="font-semibold text-light-text mb-3">Table of Contents</h3>
                <nav className="space-y-1">
                  {tableOfContents.map((item) => (
                    <a
                      key={item.id}
                      href={`#${item.id}`}
                      className={`block text-sm hover:text-light-accent transition-colors ${
                        item.level === 1 ? 'font-medium' : 
                        item.level === 2 ? 'ml-2' :
                        item.level === 3 ? 'ml-4' : 'ml-6'
                      } ${'text-light-text-secondary hover:text-light-accent'}`}
                      style={{ marginLeft: `${(item.level - 1) * 0.75}rem` }}
                    >
                      {item.text}
                    </a>
                  ))}
                </nav>
              </div>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
};

export default ArticleReader;