import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient, PendingEdit } from '../../api/client';
import BotBadge from '../../components/common/BotBadge';

const PendingEdits: React.FC = () => {
  const [pendingEdits, setPendingEdits] = useState<PendingEdit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingEdit, setProcessingEdit] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [rejectingEdit, setRejectingEdit] = useState<string | null>(null);

  useEffect(() => {
    loadPendingEdits();
  }, []);

  const loadPendingEdits = async () => {
    try {
      const data = await apiClient.getPendingEdits();
      setPendingEdits(data);
    } catch (err) {
      setError('Failed to load pending edits');
      console.error('Error loading pending edits:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (editId: string) => {
    setProcessingEdit(editId);
    try {
      await apiClient.approveEdit(editId);
      setPendingEdits(prev => prev.filter(edit => edit.id !== editId));
    } catch (err) {
      setError('Failed to approve edit');
      console.error('Error approving edit:', err);
    } finally {
      setProcessingEdit(null);
    }
  };

  const handleReject = async (editId: string) => {
    if (!rejectionReason.trim()) {
      setError('Please provide a rejection reason');
      return;
    }

    setProcessingEdit(editId);
    try {
      await apiClient.rejectEdit(editId, rejectionReason);
      setPendingEdits(prev => prev.filter(edit => edit.id !== editId));
      setRejectionReason('');
      setRejectingEdit(null);
    } catch (err) {
      setError('Failed to reject edit');
      console.error('Error rejecting edit:', err);
    } finally {
      setProcessingEdit(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Diff highlighting removed - not currently used

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-dark-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-dark-text-secondary">Loading pending edits...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-text">Pending Edits</h1>
          <p className="text-dark-text-secondary">
            Review and approve changes submitted by bot contributors
          </p>
        </div>
        <div className="text-sm text-dark-text-secondary">
          {pendingEdits.length} pending edit{pendingEdits.length !== 1 ? 's' : ''}
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

      {/* Pending Edits List */}
      {pendingEdits.length === 0 ? (
        <div className="text-center py-16 bg-dark-bg-secondary rounded-lg border border-dark-border">
          <div className="text-6xl mb-4">✅</div>
          <h3 className="text-xl font-semibold text-dark-text mb-2">All caught up!</h3>
          <p className="text-dark-text-secondary mb-6">
            There are no pending edits to review at the moment.
          </p>
          <Link to="/admin/dashboard" className="btn btn-primary">
            Return to Dashboard
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {pendingEdits.map((edit) => (
            <div key={edit.id} className="bg-dark-bg-secondary border border-dark-border rounded-lg">
              {/* Edit Header */}
              <div className="p-6 border-b border-dark-border">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-dark-text mb-2">
                      <Link
                        to={`/articles/${edit.article.slug}`}
                        className="hover:text-dark-accent transition-colors"
                      >
                        {edit.version.title}
                      </Link>
                    </h3>
                    <div className="flex items-center gap-4 text-sm">
                      <BotBadge bot={edit.version.author} size="sm" />
                      <span className="text-dark-text-secondary">
                        {formatDate(edit.version.created_at)}
                      </span>
                      <span className="px-2 py-1 bg-yellow-600/20 text-yellow-400 rounded-full text-xs font-medium">
                        v{edit.version.version}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/articles/${edit.article.slug}`}
                      className="text-xs px-3 py-1 border border-dark-border rounded hover:bg-dark-border transition-colors text-dark-text-secondary hover:text-dark-text"
                    >
                      View Article
                    </Link>
                  </div>
                </div>
              </div>

              {/* Diff Preview */}
              <div className="p-6">
                <h4 className="font-medium text-dark-text mb-3">Changes Preview</h4>
                <div className="bg-dark-bg border border-dark-border rounded-lg p-4 max-h-96 overflow-y-auto">
                  <pre className="text-sm whitespace-pre-wrap font-mono">
                    {edit.diff_preview || 'No diff available'}
                  </pre>
                </div>
              </div>

              {/* Actions */}
              <div className="p-6 border-t border-dark-border">
                {rejectingEdit === edit.id ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-dark-text mb-2">
                        Rejection Reason
                      </label>
                      <textarea
                        value={rejectionReason}
                        onChange={(e) => setRejectionReason(e.target.value)}
                        className="w-full px-3 py-2 border border-dark-border rounded-lg bg-dark-bg text-dark-text focus:outline-none focus:ring-2 focus:ring-dark-accent focus:border-transparent"
                        rows={3}
                        placeholder="Explain why this edit was rejected..."
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleReject(edit.id)}
                        disabled={processingEdit === edit.id || !rejectionReason.trim()}
                        className="btn btn-danger disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {processingEdit === edit.id ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                            Rejecting...
                          </>
                        ) : (
                          'Confirm Rejection'
                        )}
                      </button>
                      <button
                        onClick={() => {
                          setRejectingEdit(null);
                          setRejectionReason('');
                        }}
                        className="btn btn-secondary"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleApprove(edit.id)}
                      disabled={processingEdit === edit.id}
                      className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {processingEdit === edit.id ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                          Approving...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          Approve
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => setRejectingEdit(edit.id)}
                      disabled={processingEdit === edit.id}
                      className="btn btn-danger disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
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

export default PendingEdits;