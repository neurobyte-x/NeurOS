/**
 * NeurOS 2.0 Review Store (Zustand)
 */

import { create } from 'zustand';
import type { 
  ReviewQueue, 
  ReviewItemWithData, 
  ReviewStats, 
  ReviewSubmit,
  ReviewResult,
} from '../lib/types';
import { reviewsApi } from '../lib/api';

interface ReviewState {
  queue: ReviewQueue | null;
  currentItem: ReviewItemWithData | null;
  stats: ReviewStats | null;
  isLoading: boolean;
  isSubmitting: boolean;
  lastResult: ReviewResult | null;
  sessionStats: {
    reviewed: number;
    correct: number;
    startTime: number | null;
  };

  // Actions
  fetchQueue: (limit?: number) => Promise<void>;
  fetchNext: () => Promise<void>;
  submitReview: (reviewId: number, data: ReviewSubmit) => Promise<ReviewResult | null>;
  startSession: () => void;
  endSession: () => void;
  suspendItem: (reviewId: number) => Promise<void>;
}

export const useReviewStore = create<ReviewState>()((set, get) => ({
  queue: null,
  currentItem: null,
  stats: null,
  isLoading: false,
  isSubmitting: false,
  lastResult: null,
  sessionStats: {
    reviewed: 0,
    correct: 0,
    startTime: null,
  },

  fetchQueue: async (limit = 20) => {
    set({ isLoading: true });
    try {
      const queue = await reviewsApi.getQueue(limit);
      set({ 
        queue, 
        stats: queue.stats,
        currentItem: queue.next_item,
        isLoading: false,
      });
    } catch (err) {
      console.error('Failed to fetch review queue:', err);
      set({ isLoading: false });
    }
  },

  fetchNext: async () => {
    set({ isLoading: true });
    try {
      const item = await reviewsApi.getNext();
      set({ currentItem: item, isLoading: false });
    } catch (err) {
      console.error('Failed to fetch next item:', err);
      set({ isLoading: false });
    }
  },

  submitReview: async (reviewId, data) => {
    set({ isSubmitting: true });
    try {
      const result = await reviewsApi.submit(reviewId, data);
      
      // Update session stats
      const { sessionStats } = get();
      set({
        lastResult: result,
        isSubmitting: false,
        sessionStats: {
          ...sessionStats,
          reviewed: sessionStats.reviewed + 1,
          correct: data.quality >= 3 ? sessionStats.correct + 1 : sessionStats.correct,
        },
      });

      // Fetch next item
      await get().fetchNext();
      
      return result;
    } catch (err) {
      console.error('Failed to submit review:', err);
      set({ isSubmitting: false });
      return null;
    }
  },

  startSession: () => {
    set({
      sessionStats: {
        reviewed: 0,
        correct: 0,
        startTime: Date.now(),
      },
    });
  },

  endSession: () => {
    set({
      sessionStats: {
        reviewed: 0,
        correct: 0,
        startTime: null,
      },
    });
  },

  suspendItem: async (reviewId) => {
    try {
      await reviewsApi.suspend(reviewId);
      await get().fetchNext();
    } catch (err) {
      console.error('Failed to suspend item:', err);
    }
  },
}));
