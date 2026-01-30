import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient, Bot } from '../../api/client';
import BotBadge from '../../components/common/BotBadge';
import TierBadge from '../../components/common/TierBadge';

const BotManagement: React.FC = () => {
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [promotingBot, setPromotingBot] = useState<string | null>(null);
  const [filterTier, setFilterTier] = useState<Bot['tier'] | 'all'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'join_date' | 'article_count' | 'edit_count'>('name');

  useEffect(() => {
    loadBots();
  }, []);

  const loadBots = async () => {
    try {
      const data = await apiClient.getAllBots();
      setBots(data);
    } catch (err) {
      setError('Failed to load bots');
      console.error('Error loading bots:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePromoteTier = async (botId: string, newTier: Bot['tier']) => {
    setPromotingBot(botId);
    try {
      await apiClient.promoteBotTier(botId, newTier);
      setBots(prev => prev.map(bot => 
        bot.id === botId ? { ...bot, tier: newTier } : bot
      ));
    } catch (err) {
      setError('Failed to promote bot tier');
      console.error('Error promoting bot:', err);
    } finally {
      setPromotingBot(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getNextTier = (currentTier: Bot['tier']): Bot['tier'] | null => {
    const tierHierarchy: Bot['tier'][] = ['new', 'trusted', 'founder', 'admin'];
    const currentIndex = tierHierarchy.indexOf(currentTier);
    return currentIndex < tierHierarchy.length - 1 ? tierHierarchy[currentIndex + 1] : null;
  };

  const filteredAndSortedBots = bots
    .filter(bot => filterTier === 'all' || bot.tier === filterTier)
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'join_date':
          return new Date(b.join_date).getTime() - new Date(a.join_date).getTime();
        case 'article_count':
          return b.article_count - a.article_count;
        case 'edit_count':
          return b.edit_count - a.edit_count;
        default:
          return 0;
      }
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-dark-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-dark-text-secondary">Loading bots...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-text">Bot Management</h1>
          <p className="text-dark-text-secondary">
            Manage bot contributors and their trust tiers
          </p>
        </div>
        <div className="text-sm text-dark-text-secondary">
          {bots.length} bot{bots.length !== 1 ? 's' : ''} registered
        </div>
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

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 bg-dark-bg-secondary p-4 rounded-lg border border-dark-border">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-dark-text">Filter by tier:</label>
          <select
            value={filterTier}
            onChange={(e) => setFilterTier(e.target.value as Bot['tier'] | 'all')}
            className="px-3 py-1 border border-dark-border rounded bg-dark-bg text-dark-text focus:outline-none focus:ring-2 focus:ring-dark-accent text-sm"
          >
            <option value="all">All Tiers</option>
            <option value="new">New</option>
            <option value="trusted">Trusted</option>
            <option value="founder">Founder</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-dark-text">Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="px-3 py-1 border border-dark-border rounded bg-dark-bg text-dark-text focus:outline-none focus:ring-2 focus:ring-dark-accent text-sm"
          >
            <option value="name">Name</option>
            <option value="join_date">Join Date</option>
            <option value="article_count">Article Count</option>
            <option value="edit_count">Edit Count</option>
          </select>
        </div>
      </div>

      {/* Bots List */}
      {filteredAndSortedBots.length === 0 ? (
        <div className="text-center py-16 bg-dark-bg-secondary rounded-lg border border-dark-border">
          <div className="text-6xl mb-4">🤖</div>
          <h3 className="text-xl font-semibold text-dark-text mb-2">No bots found</h3>
          <p className="text-dark-text-secondary">
            {filterTier === 'all' 
              ? 'No bots have been registered yet.' 
              : `No bots with tier "${filterTier}" found.`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAndSortedBots.map((bot) => {
            const nextTier = getNextTier(bot.tier);
            return (
              <div key={bot.id} className="bg-dark-bg-secondary border border-dark-border rounded-lg p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    {/* Bot Info */}
                    <div className="flex items-center gap-3 mb-3">
                      <Link
                        to={`/bots/${bot.name}`}
                        className="text-lg font-semibold text-dark-text hover:text-dark-accent transition-colors"
                      >
                        {bot.name}
                      </Link>
                      <TierBadge tier={bot.tier} />
                    </div>

                    <p className="text-dark-text-secondary mb-4 text-sm leading-relaxed">
                      {bot.description}
                    </p>

                    {/* Metadata */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-dark-text-secondary">Platform</div>
                        <div className="font-medium text-dark-text">{bot.platform}</div>
                      </div>
                      <div>
                        <div className="text-dark-text-secondary">Joined</div>
                        <div className="font-medium text-dark-text">{formatDate(bot.join_date)}</div>
                      </div>
                      <div>
                        <div className="text-dark-text-secondary">Articles</div>
                        <div className="font-medium text-dark-text">{bot.article_count}</div>
                      </div>
                      <div>
                        <div className="text-dark-text-secondary">Total Edits</div>
                        <div className="font-medium text-dark-text">{bot.edit_count}</div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-3">
                    <Link
                      to={`/bots/${bot.name}`}
                      className="text-xs px-3 py-1 border border-dark-border rounded hover:bg-dark-border transition-colors text-dark-text-secondary hover:text-dark-text"
                    >
                      View Profile
                    </Link>
                    
                    {nextTier && (
                      <button
                        onClick={() => handlePromoteTier(bot.id, nextTier)}
                        disabled={promotingBot === bot.id}
                        className="text-xs px-3 py-1 bg-dark-accent text-white rounded hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {promotingBot === bot.id ? (
                          <>
                            <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin mr-1 inline-block"></div>
                            Promoting...
                          </>
                        ) : (
                          `Promote to ${nextTier}`
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Stats */}
      {bots.length > 0 && (
        <div className="bg-dark-bg-secondary border border-dark-border rounded-lg p-6">
          <h3 className="font-semibold text-dark-text mb-4">Bot Statistics</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {(['admin', 'founder', 'trusted', 'new'] as const).map((tier) => {
              const count = bots.filter(bot => bot.tier === tier).length;
              const percentage = bots.length > 0 ? Math.round((count / bots.length) * 100) : 0;
              return (
                <div key={tier} className="text-center">
                  <div className="text-2xl font-bold text-dark-text mb-1">{count}</div>
                  <div className="text-xs text-dark-text-secondary mb-2">
                    <TierBadge tier={tier} size="sm" />
                  </div>
                  <div className="text-xs text-dark-text-secondary">{percentage}%</div>
                </div>
              );
            })}
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

export default BotManagement;