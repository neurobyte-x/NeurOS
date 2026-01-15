/**
 * NeurOS 2.0 Review Card Component
 * Displays review items with flip animation for SRS
 */

import { useState } from 'react';
import type { ReviewItemWithData, ReviewSubmit } from '../lib/types';

interface ReviewCardProps {
  reviewItem: ReviewItemWithData;
  onSubmit: (data: ReviewSubmit) => void;
  isSubmitting: boolean;
}

export function ReviewCard({ reviewItem, onSubmit, isSubmitting }: ReviewCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [startTime] = useState(Date.now());

  const handleSubmit = (quality: number) => {
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);
    onSubmit({
      quality,
      time_spent_seconds: timeSpent,
    });
  };

  const qualityButtons = [
    { quality: 0, label: 'Again', color: 'bg-red-600', time: 'Now' },
    { quality: 2, label: 'Hard', color: 'bg-orange-500', time: '~1m' },
    { quality: 3, label: 'Good', color: 'bg-green-500', time: `${reviewItem.interval_days}d` },
    { quality: 5, label: 'Easy', color: 'bg-blue-500', time: `${Math.ceil(reviewItem.interval_days * 1.5)}d` },
  ];

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Card */}
      <div
        className={`
          relative h-80 cursor-pointer perspective-1000
          ${isFlipped ? '' : ''}
        `}
        onClick={() => !isFlipped && setIsFlipped(true)}
      >
        <div
          className={`
            absolute inset-0 transition-transform duration-500 transform-style-3d
            ${isFlipped ? 'rotate-y-180' : ''}
          `}
        >
          {/* Front */}
          <div
            className={`
              absolute inset-0 backface-hidden
              bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6
              flex flex-col items-center justify-center text-center
              ${isFlipped ? 'invisible' : ''}
            `}
          >
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
              {reviewItem.item_type.toUpperCase()}
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              {reviewItem.item_data?.title || 'Untitled'}
            </h2>
            <p className="text-gray-600 dark:text-gray-300">
              Click to reveal answer
            </p>
            <div className="mt-4 flex gap-2">
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs rounded">
                Review #{reviewItem.review_count + 1}
              </span>
              <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 text-xs rounded">
                Interval: {reviewItem.interval_days}d
              </span>
            </div>
          </div>

          {/* Back */}
          <div
            className={`
              absolute inset-0 backface-hidden rotate-y-180
              bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6
              flex flex-col
              ${!isFlipped ? 'invisible' : ''}
            `}
          >
            <div className="flex-1 overflow-auto">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {reviewItem.item_data?.title}
              </h3>
              <div className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {reviewItem.item_data?.content || 'No content available'}
              </div>
              {reviewItem.item_data?.hint && (
                <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/30 rounded">
                  <span className="text-yellow-700 dark:text-yellow-300 text-sm">
                    💡 {reviewItem.item_data.hint}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Rating Buttons (only show when flipped) */}
      {isFlipped && (
        <div className="mt-6">
          <p className="text-center text-gray-600 dark:text-gray-400 mb-3">
            How well did you remember?
          </p>
          <div className="grid grid-cols-4 gap-2">
            {qualityButtons.map(({ quality, label, color, time }) => (
              <button
                key={quality}
                onClick={() => handleSubmit(quality)}
                disabled={isSubmitting}
                className={`
                  ${color} text-white py-3 px-4 rounded-lg
                  transition hover:opacity-90 flex flex-col items-center
                  ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                <span className="font-bold">{label}</span>
                <span className="text-xs opacity-80">{time}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="mt-4 flex justify-center gap-4 text-sm text-gray-500 dark:text-gray-400">
        <span>Ease: {(reviewItem.ease_factor * 100).toFixed(0)}%</span>
        <span>Lapses: {reviewItem.lapse_count}</span>
        {reviewItem.is_leech && (
          <span className="text-red-500">⚠️ Leech</span>
        )}
      </div>
    </div>
  );
}

export default ReviewCard;
