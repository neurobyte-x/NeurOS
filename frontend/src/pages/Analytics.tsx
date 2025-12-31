import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, AlertTriangle, Calendar } from 'lucide-react';
import { analyticsApi } from '../lib/api';
import type { DailyStats, Insight } from '../lib/types';

export default function Analytics() {
  const [daily, setDaily] = useState<DailyStats | null>(null);
  const [weekly, setWeekly] = useState<any>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [blockerAnalysis, setBlockerAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [dailyRes, weeklyRes, insightsRes, blockerRes] = await Promise.all([
        analyticsApi.daily(),
        analyticsApi.weekly(),
        analyticsApi.insights(),
        analyticsApi.blockers(),
      ]);
      setDaily(dailyRes);
      setWeekly(weeklyRes);
      setInsights(insightsRes);
      setBlockerAnalysis(blockerRes);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
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
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-500 mt-1">Track your learning progress and patterns</p>
      </div>

      {/* Today's Stats */}
      {daily && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="w-5 h-5 text-primary-500" />
            <h2 className="text-lg font-semibold">Today's Activity</h2>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold">{daily.entries_total}</p>
              <p className="text-sm text-gray-500">Entries</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold">{daily.patterns_used}</p>
              <p className="text-sm text-gray-500">Patterns Used</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold">{daily.new_patterns}</p>
              <p className="text-sm text-gray-500">New Patterns</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold">{daily.total_time_minutes}</p>
              <p className="text-sm text-gray-500">Minutes</p>
            </div>
          </div>

          {daily.entries_by_type && Object.values(daily.entries_by_type).some(v => v > 0) && (
            <div className="mt-4 pt-4 border-t">
              <h3 className="text-sm font-medium text-gray-500 mb-2">By Domain</h3>
              <div className="flex gap-4">
                {Object.entries(daily.entries_by_type).map(([type, count]) => (
                  count > 0 && (
                    <span key={type} className={`badge badge-${type}`}>
                      {type}: {count as number}
                    </span>
                  )
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Weekly Overview */}
      {weekly && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold">This Week</h2>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{weekly.total_entries}</p>
              <p className="text-sm text-blue-600">Total Entries</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{weekly.total_time_minutes}</p>
              <p className="text-sm text-green-600">Minutes Spent</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-purple-600 capitalize">
                {weekly.most_active_domain?.replace('_', '/') || 'N/A'}
              </p>
              <p className="text-sm text-purple-600">Most Active Domain</p>
            </div>
          </div>

          {/* Daily Breakdown */}
          <h3 className="text-sm font-medium text-gray-500 mb-2">Daily Activity</h3>
          <div className="flex gap-2 items-end h-32">
            {weekly.daily_breakdown?.map((day: DailyStats, i: number) => {
              const height = day.entries_total > 0 
                ? Math.max(20, (day.entries_total / Math.max(...weekly.daily_breakdown.map((d: DailyStats) => d.entries_total || 1))) * 100)
                : 10;
              return (
                <div key={i} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-primary-500 rounded-t"
                    style={{ height: `${height}%` }}
                  />
                  <span className="text-xs text-gray-500 mt-1">
                    {new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Insights */}
      {insights.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-green-500" />
            <h2 className="text-lg font-semibold">Insights</h2>
          </div>

          <div className="space-y-3">
            {insights.map((insight, i) => (
              <div
                key={i}
                className={`p-4 rounded-lg ${
                  insight.type === 'weakness' ? 'bg-red-50 border-l-4 border-red-500' :
                  insight.type === 'strength' ? 'bg-green-50 border-l-4 border-green-500' :
                  insight.type === 'progress' ? 'bg-blue-50 border-l-4 border-blue-500' :
                  'bg-gray-50 border-l-4 border-gray-400'
                }`}
              >
                <h3 className="font-medium">{insight.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Blocker Analysis */}
      {blockerAnalysis && blockerAnalysis.top_blockers?.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            <h2 className="text-lg font-semibold">Blocker Analysis</h2>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-yellow-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-yellow-600">{blockerAnalysis.total_unique_blockers}</p>
              <p className="text-sm text-yellow-600">Unique Blockers</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-red-600">{blockerAnalysis.flagged_blockers}</p>
              <p className="text-sm text-red-600">Flagged (Repeated)</p>
            </div>
          </div>

          <h3 className="text-sm font-medium text-gray-500 mb-2">Top Blockers</h3>
          <div className="space-y-2">
            {blockerAnalysis.top_blockers.map((blocker: any, i: number) => (
              <div
                key={i}
                className={`p-3 rounded-lg ${blocker.is_flagged ? 'bg-red-50' : 'bg-gray-50'}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm">{blocker.text}</span>
                  <span className={`badge ${blocker.is_flagged ? 'bg-red-100 text-red-800' : 'bg-gray-200 text-gray-600'}`}>
                    {blocker.count}x
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {(!daily || daily.entries_total === 0) && (!weekly || weekly.total_entries === 0) && (
        <div className="text-center py-12 text-gray-500">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium">No data yet</h3>
          <p className="mt-1">Start creating entries to see your analytics</p>
        </div>
      )}
    </div>
  );
}
