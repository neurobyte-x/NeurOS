import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  PlusCircle, 
  AlertTriangle, 
  TrendingUp,
  Flame,
  Brain,
  Target,
  Sparkles
} from 'lucide-react';
import { entriesApi, analyticsApi } from '../lib/api';
import EntryCard from '../components/EntryCard';
import type { Entry, Insight } from '../lib/types';

export default function Dashboard() {
  const [recentEntries, setRecentEntries] = useState<Entry[]>([]);
  const [incompleteEntries, setIncompleteEntries] = useState<Entry[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [streak, setStreak] = useState<{ streak_days: number; message: string } | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [entriesRes, incomplete, insightsRes, streakRes, statsRes] = await Promise.all([
        entriesApi.list({ page_size: 5, is_complete: true }),
        entriesApi.incomplete(),
        analyticsApi.insights(),
        analyticsApi.streak(),
        entriesApi.stats(),
      ]);

      setRecentEntries(entriesRes.entries);
      setIncompleteEntries(incomplete);
      setInsights(insightsRes);
      setStreak(streakRes);
      setStats(statsRes);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Your learning at a glance</p>
        </div>
        <Link to="/new" className="btn-primary flex items-center gap-2">
          <PlusCircle className="w-5 h-5" />
          New Entry
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Entries</p>
              <p className="text-2xl font-bold">{stats?.total_entries || 0}</p>
            </div>
            <Brain className="w-8 h-8 text-primary-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Complete</p>
              <p className="text-2xl font-bold text-green-600">{stats?.complete_entries || 0}</p>
            </div>
            <Target className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Streak</p>
              <p className="text-2xl font-bold text-orange-600">{streak?.streak_days || 0} days</p>
            </div>
            <Flame className="w-8 h-8 text-orange-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Avg Time</p>
              <p className="text-2xl font-bold">{stats?.avg_time_spent_minutes || 0} min</p>
            </div>
            <TrendingUp className="w-8 h-8 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Incomplete Entries Warning */}
      {incompleteEntries.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-800">
                {incompleteEntries.length} entries need reflection
              </h3>
              <p className="text-sm text-yellow-700 mt-1">
                Complete your reflections to solidify learning. No reflection = no persistence!
              </p>
              <div className="mt-4 space-y-2">
                {incompleteEntries.slice(0, 3).map(entry => (
                  <Link
                    key={entry.id}
                    to={`/entry/${entry.id}`}
                    className="block bg-white rounded-lg p-3 hover:bg-yellow-100 transition-colors"
                  >
                    <span className="font-medium text-gray-900">{entry.title}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Recommendation & Active Plans */}
      <div className="grid grid-cols-2 gap-6">
        {/* Quick Actions */}
        <div className="card bg-gradient-to-br from-primary-50 to-blue-50 border-primary-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary-500" />
              Quick Actions
            </h2>
          </div>
          <div className="space-y-3">
            <Link to="/new" className="block p-3 bg-white rounded-lg hover:bg-gray-50 transition-colors border">
              <div className="flex items-center gap-2">
                <PlusCircle className="w-5 h-5 text-primary-500" />
                <span className="font-medium">Log New Learning</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">Capture what you learned today</p>
            </Link>
            <Link to="/recall" className="block p-3 bg-white rounded-lg hover:bg-gray-50 transition-colors border">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-500" />
                <span className="font-medium">Practice Recall</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">Test your memory on past entries</p>
            </Link>
            <Link to="/patterns" className="block p-3 bg-white rounded-lg hover:bg-gray-50 transition-colors border">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-green-500" />
                <span className="font-medium">View Patterns</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">See patterns you've discovered</p>
            </Link>
          </div>
        </div>
      </div>

      {/* Insights */}
      {insights.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">💡 Insights</h2>
          <div className="space-y-3">
            {insights.map((insight, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg ${
                  insight.type === 'weakness' ? 'bg-red-50' :
                  insight.type === 'strength' ? 'bg-green-50' :
                  insight.type === 'progress' ? 'bg-blue-50' :
                  'bg-gray-50'
                }`}
              >
                <h4 className="font-medium">{insight.title}</h4>
                <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Entries */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Entries</h2>
          <Link to="/entries" className="text-primary-600 hover:text-primary-700 text-sm">
            View all →
          </Link>
        </div>
        
        {recentEntries.length > 0 ? (
          <div className="grid grid-cols-2 gap-4">
            {recentEntries.map(entry => (
              <EntryCard key={entry.id} entry={entry} />
            ))}
          </div>
        ) : (
          <div className="card text-center py-12">
            <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-600">No entries yet</h3>
            <p className="text-gray-500 mt-1">Start capturing your learning!</p>
            <Link to="/new" className="btn-primary inline-flex items-center gap-2 mt-4">
              <PlusCircle className="w-5 h-5" />
              Create First Entry
            </Link>
          </div>
        )}
      </div>

      {/* Domain Distribution */}
      {stats?.entries_by_type && Object.values(stats.entries_by_type).some((v: any) => v > 0) && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">📊 Domain Distribution</h2>
          <div className="grid grid-cols-4 gap-4">
            {Object.entries(stats.entries_by_type).map(([type, count]) => (
              <div key={type} className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold">{count as number}</p>
                <p className="text-sm text-gray-500 capitalize">{type.replace('_', '/')}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
