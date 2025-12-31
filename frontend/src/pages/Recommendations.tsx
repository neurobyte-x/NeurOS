import { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Target, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  Zap,
  BookOpen,
  Code2,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  ExternalLink,
  Star,
  Loader2
} from 'lucide-react';
import { recommendationsApi } from '../lib/api';
import type { 
  Recommendation, 
  SkillGapAnalysis, 
  QuickRecommendation,
  RecommendationDomain 
} from '../lib/types';

const PRIORITY_COLORS = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-blue-100 text-blue-800 border-blue-200',
  low: 'bg-gray-100 text-gray-800 border-gray-200',
};

const TYPE_ICONS: Record<string, JSX.Element> = {
  problem: <Code2 className="w-4 h-4" />,
  concept: <BookOpen className="w-4 h-4" />,
  resource: <ExternalLink className="w-4 h-4" />,
  practice: <Target className="w-4 h-4" />,
  revision: <RefreshCw className="w-4 h-4" />,
  project: <Zap className="w-4 h-4" />,
  challenge: <TrendingUp className="w-4 h-4" />,
};

const DOMAIN_COLORS: Record<string, string> = {
  dsa: 'bg-blue-500',
  cp: 'bg-purple-500',
  backend: 'bg-green-500',
  ai_ml: 'bg-pink-500',
  system_design: 'bg-yellow-500',
  general: 'bg-gray-500',
};

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [skillGaps, setSkillGaps] = useState<SkillGapAnalysis[]>([]);
  const [quickRec, setQuickRec] = useState<QuickRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedDomains, setSelectedDomains] = useState<RecommendationDomain[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'active' | 'completed' | 'dismissed'>('active');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [dashboard, gaps] = await Promise.all([
        recommendationsApi.getDashboard(),
        recommendationsApi.getSkillGaps().catch(() => []),
      ]);
      
      setRecommendations(dashboard.active_recommendations || []);
      setSkillGaps(gaps);
      setQuickRec(dashboard.daily_suggestion);
      setStats(dashboard.stats);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecommendations = async (filter?: { is_completed?: boolean }) => {
    try {
      const result = await recommendationsApi.list({
        is_completed: filter?.is_completed,
        page_size: 50
      });
      setRecommendations(result.recommendations || []);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  };

  const generateRecommendations = async () => {
    setGenerating(true);
    try {
      const newRecs = await recommendationsApi.generate({
        domains: selectedDomains.length > 0 ? selectedDomains : undefined,
        count: 5,
        include_revisions: true,
      });
      setRecommendations(prev => [...newRecs, ...prev]);
    } catch (error) {
      console.error('Failed to generate recommendations:', error);
    } finally {
      setGenerating(false);
    }
  };

  const getQuickRecommendation = async (minutes: number = 30) => {
    try {
      const rec = await recommendationsApi.getQuick(minutes);
      setQuickRec(rec);
    } catch (error) {
      console.error('Failed to get quick recommendation:', error);
    }
  };

  const completeRecommendation = async (id: number) => {
    try {
      await recommendationsApi.complete(id);
      setRecommendations(prev => prev.filter(r => r.id !== id));
    } catch (error) {
      console.error('Failed to complete recommendation:', error);
    }
  };

  const dismissRecommendation = async (id: number) => {
    try {
      await recommendationsApi.dismiss(id);
      setRecommendations(prev => prev.filter(r => r.id !== id));
    } catch (error) {
      console.error('Failed to dismiss recommendation:', error);
    }
  };

  const toggleDomain = (domain: RecommendationDomain) => {
    setSelectedDomains(prev => 
      prev.includes(domain) 
        ? prev.filter(d => d !== domain)
        : [...prev, domain]
    );
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
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-primary-500" />
            Recommendations
          </h1>
          <p className="text-gray-500 mt-1">
            AI-powered suggestions based on your learning journey
          </p>
        </div>
        <button
          onClick={generateRecommendations}
          disabled={generating}
          className="btn-primary flex items-center gap-2"
        >
          {generating ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Sparkles className="w-5 h-5" />
          )}
          Generate New
        </button>
      </div>

      {/* Quick Recommendation Card */}
      {quickRec && (
        <div className="card bg-gradient-to-r from-primary-50 to-blue-50 border-primary-200">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-primary-100 rounded-lg">
                <Zap className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-primary-600 mb-1">Quick Suggestion</p>
                <h3 className="text-lg font-semibold text-gray-900">{quickRec.title}</h3>
                <p className="text-gray-600 mt-1">{quickRec.description}</p>
                <p className="text-sm text-gray-500 mt-2 italic">💡 {quickRec.reasoning}</p>
                {quickRec.resource_url && (
                  <a
                    href={quickRec.resource_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-2 text-primary-600 hover:underline"
                  >
                    Open Resource <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              {[15, 30, 60].map(mins => (
                <button
                  key={mins}
                  onClick={() => getQuickRecommendation(mins)}
                  className="px-3 py-1 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  {mins}m
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total</p>
                <p className="text-2xl font-bold">{stats.total || 0}</p>
              </div>
              <Target className="w-8 h-8 text-gray-400" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Completed</p>
                <p className="text-2xl font-bold text-green-600">{stats.completed || 0}</p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Dismissed</p>
                <p className="text-2xl font-bold text-gray-600">{stats.dismissed || 0}</p>
              </div>
              <XCircle className="w-8 h-8 text-gray-400" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Completion Rate</p>
                <p className="text-2xl font-bold text-primary-600">
                  {stats.completion_rate?.toFixed(0) || 0}%
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-primary-500" />
            </div>
          </div>
        </div>
      )}

      {/* Skill Gaps Analysis */}
      {skillGaps.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Skill Gap Analysis
          </h2>
          <div className="grid grid-cols-2 gap-4">
            {skillGaps.map((gap, idx) => (
              <div key={idx} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium capitalize">{gap.domain}</span>
                  <span className="text-sm text-gray-500">Level {gap.current_level}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                  <div 
                    className={`h-2 rounded-full ${DOMAIN_COLORS[gap.domain] || 'bg-gray-500'}`}
                    style={{ width: `${gap.current_level * 10}%` }}
                  />
                </div>
                <div className="space-y-2 text-sm">
                  {gap.identified_gaps?.length > 0 && (
                    <div>
                      <span className="text-red-600 font-medium">Gaps: </span>
                      {gap.identified_gaps.slice(0, 3).join(', ')}
                    </div>
                  )}
                  {gap.strengths?.length > 0 && (
                    <div>
                      <span className="text-green-600 font-medium">Strengths: </span>
                      {gap.strengths.slice(0, 3).join(', ')}
                    </div>
                  )}
                  <div className="pt-2 border-t border-gray-200">
                    <span className="text-primary-600 font-medium">Focus: </span>
                    {gap.suggested_focus}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Domain Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm text-gray-500">Filter by domain:</span>
        {(['dsa', 'cp', 'backend', 'ai_ml', 'system_design'] as RecommendationDomain[]).map(domain => (
          <button
            key={domain}
            onClick={() => toggleDomain(domain)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selectedDomains.includes(domain)
                ? `${DOMAIN_COLORS[domain]} text-white`
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {domain.toUpperCase().replace('_', '/')}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-8">
          {(['active', 'completed', 'dismissed'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                if (tab === 'active') loadDashboard();
                else loadRecommendations({ is_completed: tab === 'completed' });
              }}
              className={`pb-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {recommendations.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No recommendations yet.</p>
            <p className="text-sm">Click "Generate New" to get personalized suggestions!</p>
          </div>
        ) : (
          recommendations.map(rec => (
            <div
              key={rec.id}
              className={`card hover:shadow-md transition-shadow border-l-4 ${
                PRIORITY_COLORS[rec.priority]?.split(' ')[2] || 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div className={`p-2 rounded-lg ${DOMAIN_COLORS[rec.domain]} bg-opacity-10`}>
                    {TYPE_ICONS[rec.rec_type] || <Target className="w-5 h-5" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">{rec.title}</h3>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${PRIORITY_COLORS[rec.priority]}`}>
                        {rec.priority}
                      </span>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${DOMAIN_COLORS[rec.domain]} text-white`}>
                        {rec.domain.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-600 text-sm mb-2">{rec.description}</p>
                    <p className="text-sm text-gray-500 italic mb-2">💡 {rec.reasoning}</p>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      {rec.estimated_minutes && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {rec.estimated_minutes} min
                        </span>
                      )}
                      {rec.difficulty_level && (
                        <span className="flex items-center gap-1">
                          <Star className="w-4 h-4" />
                          Difficulty {rec.difficulty_level}/5
                        </span>
                      )}
                      {rec.resource_url && (
                        <a
                          href={rec.resource_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-primary-600 hover:underline"
                        >
                          <ExternalLink className="w-4 h-4" />
                          {rec.resource_name || 'Open'}
                        </a>
                      )}
                    </div>

                    {rec.related_patterns?.length > 0 && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-gray-500">Patterns:</span>
                        {rec.related_patterns.map((pattern, idx) => (
                          <span key={idx} className="px-2 py-0.5 text-xs bg-gray-100 rounded">
                            {pattern}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {activeTab === 'active' && (
                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => completeRecommendation(rec.id)}
                      className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                      title="Mark as completed"
                    >
                      <CheckCircle2 className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => dismissRecommendation(rec.id)}
                      className="p-2 text-gray-400 hover:bg-gray-50 rounded-lg"
                      title="Dismiss"
                    >
                      <XCircle className="w-5 h-5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}