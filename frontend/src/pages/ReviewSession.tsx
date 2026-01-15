/**
 * NeurOS 2.0 Review Session Page
 * Spaced Repetition System interface
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useReviewStore } from '../stores/reviewStore';
import { ReviewCard } from '../components/ReviewCard';
import { FlashCodingEditor } from '../components/FlashCodingEditor';
import type { ReviewSubmit } from '../lib/types';

export function ReviewSession() {
  const navigate = useNavigate();
  const {
    queue,
    currentItem,
    stats,
    isLoading,
    isSubmitting,
    lastResult,
    sessionStats,
    fetchQueue,
    submitReview,
    startSession,
    endSession,
  } = useReviewStore();

  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    startSession();
    fetchQueue();
    return () => endSession();
  }, [fetchQueue, startSession, endSession]);

  useEffect(() => {
    if (lastResult) {
      setShowResult(true);
      const timer = setTimeout(() => setShowResult(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [lastResult]);

  const handleSubmit = async (data: ReviewSubmit) => {
    if (currentItem) {
      await submitReview(currentItem.id, data);
    }
  };

  if (isLoading && !currentItem) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading reviews...</p>
        </div>
      </div>
    );
  }

  if (!currentItem && stats?.due_now === 0) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md p-8">
          <div className="text-6xl mb-4">🎉</div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            All caught up!
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            You've completed all your reviews for now. Great work!
          </p>
          
          {sessionStats.reviewed > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 mb-6 shadow">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Session Summary
              </h3>
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-blue-600">{sessionStats.reviewed}</div>
                  <div className="text-sm text-gray-500">Reviewed</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {sessionStats.reviewed > 0
                      ? Math.round((sessionStats.correct / sessionStats.reviewed) * 100)
                      : 0}%
                  </div>
                  <div className="text-sm text-gray-500">Accuracy</div>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const isFlashCoding = currentItem?.item_type === 'pattern';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              ← Back
            </button>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Review Session
            </h1>
          </div>
          
          {stats && (
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-red-500 rounded-full" />
                <span className="text-gray-600 dark:text-gray-400">Due: {stats.due_now}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-blue-500 rounded-full" />
                <span className="text-gray-600 dark:text-gray-400">Learning: {stats.learning}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-green-500 rounded-full" />
                <span className="text-gray-600 dark:text-gray-400">Done: {sessionStats.reviewed}</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Result Toast */}
        {showResult && lastResult && (
          <div
            className={`
              fixed top-20 right-4 px-4 py-2 rounded-lg shadow-lg
              ${lastResult.is_graduated ? 'bg-green-500' : 'bg-blue-500'}
              text-white animate-fade-in-up
            `}
          >
            {lastResult.message}
            <span className="ml-2">
              Next: {lastResult.next_interval_days}d
            </span>
          </div>
        )}

        {currentItem && (
          <>
            {isFlashCoding ? (
              <FlashCodingEditor
                reviewItem={currentItem}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
              />
            ) : (
              <ReviewCard
                reviewItem={currentItem}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
              />
            )}
          </>
        )}
      </main>

      {/* Progress Bar */}
      {stats && stats.due_today > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
              <span>Progress</span>
              <span>{sessionStats.reviewed} / {sessionStats.reviewed + stats.due_now} completed</span>
            </div>
            <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-300"
                style={{
                  width: `${(sessionStats.reviewed / (sessionStats.reviewed + stats.due_now)) * 100}%`,
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReviewSession;
