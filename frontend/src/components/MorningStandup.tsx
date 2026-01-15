/**
 * NeurOS 2.0 Morning Standup Component
 * Daily intelligence briefing for personalized learning
 */

import type { DailyPlan, StandupItem } from '../lib/types';

interface MorningStandupProps {
  plan: DailyPlan;
  onStartItem: (item: StandupItem) => void;
  onDismiss: () => void;
}

function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 border-red-200 dark:border-red-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800';
    default:
      return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800';
  }
}

function getTypeIcon(type: string): string {
  switch (type) {
    case 'review':
      return '🔄';
    case 'decay':
      return '⚠️';
    case 'continue':
      return '▶️';
    case 'new':
      return '✨';
    default:
      return '📝';
  }
}

export function MorningStandup({ plan, onStartItem, onDismiss }: MorningStandupProps) {
  const now = new Date();
  const hour = now.getHours();
  
  const timeOfDay = hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-auto bg-gradient-to-br from-indigo-900 to-purple-900 rounded-2xl shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-white/10">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-white mb-1">
                Good {timeOfDay}! 👋
              </h1>
              <p className="text-indigo-200">
                {new Date(plan.date).toLocaleDateString('en-US', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>
            <button
              onClick={onDismiss}
              className="text-white/60 hover:text-white transition"
              aria-label="Close"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Summary */}
        <div className="p-6 border-b border-white/10">
          <p className="text-xl text-white">{plan.greeting}</p>
          <p className="mt-2 text-indigo-200">{plan.summary}</p>
          
          <div className="mt-4 flex gap-4">
            <div className="bg-white/10 rounded-lg px-4 py-2">
              <div className="text-2xl font-bold text-white">{plan.items.length}</div>
              <div className="text-xs text-indigo-200">Tasks</div>
            </div>
            <div className="bg-white/10 rounded-lg px-4 py-2">
              <div className="text-2xl font-bold text-white">{plan.total_estimated_minutes}</div>
              <div className="text-xs text-indigo-200">Minutes</div>
            </div>
            <div className="bg-white/10 rounded-lg px-4 py-2 flex-1">
              <div className="text-sm font-bold text-white">Focus Area</div>
              <div className="text-xs text-indigo-200">{plan.focus_area}</div>
            </div>
          </div>
        </div>

        {/* Tasks */}
        <div className="p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Today's Plan</h2>
          <div className="space-y-3">
            {plan.items.map((item, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border ${getPriorityColor(item.priority)} cursor-pointer hover:scale-[1.02] transition-transform`}
                onClick={() => onStartItem(item)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{getTypeIcon(item.type)}</span>
                    <div>
                      <h3 className="font-semibold">{item.title}</h3>
                      <p className="text-sm opacity-80">{item.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium">
                      ~{item.estimated_minutes}m
                    </span>
                    <div className="text-xs opacity-60 capitalize">
                      {item.priority}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quote */}
        <div className="p-6 border-t border-white/10">
          <div className="flex items-start gap-3">
            <span className="text-2xl">💡</span>
            <blockquote className="text-indigo-200 italic">
              "{plan.motivational_quote}"
            </blockquote>
          </div>
        </div>

        {/* Actions */}
        <div className="p-6 border-t border-white/10 flex gap-3">
          <button
            onClick={() => plan.items[0] && onStartItem(plan.items[0])}
            className="flex-1 bg-white text-indigo-900 font-semibold py-3 rounded-lg hover:bg-indigo-100 transition"
          >
            Start First Task
          </button>
          <button
            onClick={onDismiss}
            className="px-6 bg-white/10 text-white font-semibold py-3 rounded-lg hover:bg-white/20 transition"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

export default MorningStandup;
