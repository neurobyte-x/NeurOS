/**
 * NeurOS 2.0 Decay Dashboard Component
 * Visualizes knowledge decay with alerts and heatmap
 */

import { useMemo } from 'react';
import type { DecayOverview, DecayCriticalAlert, PracticeHeatmap, HeatmapDay } from '../lib/types';

interface DecayDashboardProps {
  overview: DecayOverview;
  criticalItems: DecayCriticalAlert[];
  heatmap: PracticeHeatmap;
  onPractice: (itemId: number, type: string) => void;
}

function getHeatmapColor(level: number): string {
  const colors = [
    'bg-gray-100 dark:bg-gray-800', // 0
    'bg-green-200 dark:bg-green-900', // 1
    'bg-green-400 dark:bg-green-700', // 2
    'bg-green-500 dark:bg-green-600', // 3
    'bg-green-600 dark:bg-green-500', // 4
  ];
  return colors[level] || colors[0];
}

function HeatmapGrid({ days }: { days: HeatmapDay[] }) {
  const weeks = useMemo(() => {
    const result: HeatmapDay[][] = [];
    let currentWeek: HeatmapDay[] = [];

    // Fill in starting empty days
    if (days.length > 0) {
      const firstDate = new Date(days[0].date);
      const dayOfWeek = firstDate.getDay();
      for (let i = 0; i < dayOfWeek; i++) {
        currentWeek.push({ date: '', count: 0, level: 0 });
      }
    }

    days.forEach((day) => {
      currentWeek.push(day);
      if (currentWeek.length === 7) {
        result.push(currentWeek);
        currentWeek = [];
      }
    });

    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) {
        currentWeek.push({ date: '', count: 0, level: 0 });
      }
      result.push(currentWeek);
    }

    return result;
  }, [days]);

  return (
    <div className="flex gap-1 overflow-x-auto pb-2">
      {weeks.map((week, weekIndex) => (
        <div key={weekIndex} className="flex flex-col gap-1">
          {week.map((day, dayIndex) => (
            <div
              key={dayIndex}
              className={`w-3 h-3 rounded-sm ${getHeatmapColor(day.level)} ${
                day.date ? 'cursor-pointer hover:ring-1 hover:ring-gray-400' : ''
              }`}
              title={day.date ? `${day.date}: ${day.count} practices` : ''}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export function DecayDashboard({
  overview,
  criticalItems,
  heatmap,
  onPractice,
}: DecayDashboardProps) {
  const healthPercent = overview.total_items > 0
    ? Math.round((overview.healthy_count / overview.total_items) * 100)
    : 100;

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <div className="text-3xl font-bold text-green-500">{overview.healthy_count}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Healthy</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <div className="text-3xl font-bold text-yellow-500">{overview.warning_count}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Warning</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <div className="text-3xl font-bold text-red-500">{overview.critical_count}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Critical</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <div className="text-3xl font-bold text-blue-500">{overview.items_needing_review}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Need Review</div>
        </div>
      </div>

      {/* Health Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Knowledge Health
          </span>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {healthPercent}%
          </span>
        </div>
        <div className="w-full h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              healthPercent > 70 ? 'bg-green-500' : healthPercent > 40 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${healthPercent}%` }}
          />
        </div>
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Average decay score: {overview.average_decay_score.toFixed(1)}%
        </div>
      </div>

      {/* Critical Alerts */}
      {criticalItems.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <h3 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
            <span>⚠️</span> Critical Items
          </h3>
          <div className="space-y-3">
            {criticalItems.map((alert, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/30 rounded-lg"
              >
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {alert.title}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {alert.recommended_action}
                  </div>
                  <div className="text-xs text-red-600 dark:text-red-400 mt-1">
                    Decay: {alert.decay_score.toFixed(1)}% • {Math.round(alert.hours_until_critical)}h until critical
                  </div>
                </div>
                <button
                  onClick={() => onPractice(alert.item.trackable_id, alert.item.trackable_type)}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition"
                >
                  Practice Now
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Practice Heatmap */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Practice Activity
          </h3>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-500 dark:text-gray-400">
              🔥 {heatmap.current_streak} day streak
            </span>
            <span className="text-gray-500 dark:text-gray-400">
              🏆 Best: {heatmap.longest_streak} days
            </span>
          </div>
        </div>

        <HeatmapGrid days={heatmap.days} />

        <div className="flex justify-between items-center mt-4">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {heatmap.total_practices} total practices
          </span>
          <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
            <span>Less</span>
            <div className={`w-3 h-3 rounded-sm ${getHeatmapColor(0)}`} />
            <div className={`w-3 h-3 rounded-sm ${getHeatmapColor(1)}`} />
            <div className={`w-3 h-3 rounded-sm ${getHeatmapColor(2)}`} />
            <div className={`w-3 h-3 rounded-sm ${getHeatmapColor(3)}`} />
            <div className={`w-3 h-3 rounded-sm ${getHeatmapColor(4)}`} />
            <span>More</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DecayDashboard;
