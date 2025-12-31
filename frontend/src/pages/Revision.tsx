import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCw, Brain, CheckCircle, Clock } from 'lucide-react';
import { analyticsApi } from '../lib/api';
import type { RevisionItem } from '../lib/types';

/**
 * Revision page - spaced repetition interface.
 * 
 * WHY: Regular revision solidifies learning.
 * This page surfaces items due for review.
 */
export default function Revision() {
  const [queue, setQueue] = useState<RevisionItem[]>([]);
  const [currentItem, setCurrentItem] = useState<RevisionItem | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    try {
      const data = await analyticsApi.revisionQueue();
      setQueue(data);
      if (data.length > 0) {
        setCurrentItem(data[0]);
      }
    } catch (error) {
      console.error('Failed to load revision queue:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRecall = async (quality: number) => {
    if (!currentItem) return;

    setSubmitting(true);
    try {
      await analyticsApi.recordRevision({
        entry_id: currentItem.type === 'entry' ? currentItem.id : undefined,
        pattern_id: currentItem.type === 'pattern' ? currentItem.id : undefined,
        revision_type: currentItem.type,
        recall_quality: quality,
      });

      // Move to next item
      const newQueue = queue.filter(item => item.id !== currentItem.id);
      setQueue(newQueue);
      setCurrentItem(newQueue.length > 0 ? newQueue[0] : null);
      setShowAnswer(false);
    } catch (error) {
      console.error('Failed to record revision:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Revision</h1>
        <p className="text-gray-500 mt-1">
          Strengthen your memory through spaced repetition
        </p>
      </div>

      {/* Queue Status */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-primary-500" />
            <span className="font-semibold">Items Due for Review</span>
          </div>
          <span className="badge bg-primary-100 text-primary-800">
            {queue.length} items
          </span>
        </div>
      </div>

      {/* Current Review Item */}
      {currentItem ? (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <span className={`badge ${currentItem.type === 'entry' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}`}>
              {currentItem.type === 'entry' ? 'Entry' : 'Pattern'}
            </span>
            {currentItem.due_since > 0 && (
              <span className="text-sm text-gray-500 flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {currentItem.due_since} days overdue
              </span>
            )}
          </div>

          <h2 className="text-xl font-bold text-gray-900 mb-4">
            {currentItem.title}
          </h2>

          {!showAnswer ? (
            <div className="space-y-4">
              <div className="bg-gray-50 p-6 rounded-lg text-center">
                <Brain className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600">
                  Try to recall the key pattern and insights...
                </p>
              </div>

              <button
                onClick={() => setShowAnswer(true)}
                className="btn-primary w-full py-3"
              >
                Show Details
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {currentItem.key_pattern && (
                <div className="bg-primary-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-primary-700 mb-1">Key Pattern</h3>
                  <p className="text-primary-900 font-semibold">{currentItem.key_pattern}</p>
                </div>
              )}

              {currentItem.description && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Description</h3>
                  <p className="text-gray-800">{currentItem.description}</p>
                </div>
              )}

              <Link
                to={currentItem.type === 'entry' ? `/entry/${currentItem.id}` : '/patterns'}
                className="text-primary-600 hover:underline text-sm"
              >
                View full {currentItem.type} →
              </Link>

              <hr />

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  How well did you recall this?
                </h3>

                <div className="grid grid-cols-5 gap-2">
                  {[
                    { value: 1, label: 'Forgot', color: 'red' },
                    { value: 2, label: 'Hard', color: 'orange' },
                    { value: 3, label: 'Okay', color: 'yellow' },
                    { value: 4, label: 'Good', color: 'green' },
                    { value: 5, label: 'Easy', color: 'blue' },
                  ].map(option => (
                    <button
                      key={option.value}
                      onClick={() => handleRecall(option.value)}
                      disabled={submitting}
                      className={`p-3 rounded-lg border-2 transition-colors ${
                        option.color === 'red' ? 'border-red-200 hover:border-red-400 hover:bg-red-50' :
                        option.color === 'orange' ? 'border-orange-200 hover:border-orange-400 hover:bg-orange-50' :
                        option.color === 'yellow' ? 'border-yellow-200 hover:border-yellow-400 hover:bg-yellow-50' :
                        option.color === 'green' ? 'border-green-200 hover:border-green-400 hover:bg-green-50' :
                        'border-blue-200 hover:border-blue-400 hover:bg-blue-50'
                      } disabled:opacity-50`}
                    >
                      <p className="font-medium text-gray-900">{option.value}</p>
                      <p className="text-xs text-gray-500">{option.label}</p>
                    </button>
                  ))}
                </div>

                <p className="text-xs text-gray-500 mt-2 text-center">
                  Better recall = longer interval before next review
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="card text-center py-12">
          <CheckCircle className="w-12 h-12 mx-auto text-green-500 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">All caught up!</h2>
          <p className="text-gray-500 mt-2">
            No items due for revision. Keep learning!
          </p>
          <Link to="/new" className="btn-primary inline-block mt-4">
            Create New Entry
          </Link>
        </div>
      )}

      {/* Upcoming Reviews */}
      {queue.length > 1 && (
        <div className="card">
          <h3 className="font-semibold mb-3">Up Next</h3>
          <div className="space-y-2">
            {queue.slice(1, 6).map(item => (
              <div key={item.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="text-sm">{item.title}</span>
                <span className={`badge ${item.type === 'entry' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}`}>
                  {item.type}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
