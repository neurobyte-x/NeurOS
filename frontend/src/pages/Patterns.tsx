import { useState, useEffect } from 'react';
import { Plus, Search, TrendingUp, Layers } from 'lucide-react';
import { patternsApi } from '../lib/api';
import type { Pattern, PatternCreate } from '../lib/types';

export default function Patterns() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [crossDomain, setCrossDomain] = useState<Pattern[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newPattern, setNewPattern] = useState<PatternCreate>({
    name: '',
    description: '',
    domain_tags: '',
    common_triggers: '',
    common_mistakes: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (search) {
      searchPatterns();
    } else {
      loadPatterns();
    }
  }, [search]);

  const loadData = async () => {
    try {
      const [patternsRes, crossDomainRes, statsRes] = await Promise.all([
        patternsApi.list({ sort_by: 'usage_count' }),
        patternsApi.crossDomain(),
        patternsApi.stats(),
      ]);
      setPatterns(patternsRes);
      setCrossDomain(crossDomainRes);
      setStats(statsRes);
    } catch (error) {
      console.error('Failed to load patterns:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPatterns = async () => {
    try {
      const data = await patternsApi.list({ sort_by: 'usage_count' });
      setPatterns(data);
    } catch (error) {
      console.error('Failed to load patterns:', error);
    }
  };

  const searchPatterns = async () => {
    try {
      const data = await patternsApi.search(search);
      setPatterns(data);
    } catch (error) {
      console.error('Failed to search patterns:', error);
    }
  };

  const handleCreatePattern = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPattern.name.trim()) return;

    try {
      await patternsApi.create(newPattern);
      setShowCreate(false);
      setNewPattern({
        name: '',
        description: '',
        domain_tags: '',
        common_triggers: '',
        common_mistakes: '',
      });
      loadData();
    } catch (error) {
      console.error('Failed to create pattern:', error);
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
          <h1 className="text-3xl font-bold text-gray-900">Patterns</h1>
          <p className="text-gray-500 mt-1">Your vocabulary of thinking patterns</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          New Pattern
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Patterns</p>
                <p className="text-2xl font-bold">{stats.total_patterns}</p>
              </div>
              <Layers className="w-8 h-8 text-primary-500" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Cross-Domain</p>
                <p className="text-2xl font-bold text-purple-600">{crossDomain.length}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Unused</p>
                <p className="text-2xl font-bold text-gray-400">{stats.unused_patterns}</p>
              </div>
              <Layers className="w-8 h-8 text-gray-300" />
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          className="input pl-12"
          placeholder="Search patterns..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Cross-Domain Patterns */}
      {crossDomain.length > 0 && !search && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">🌐 Cross-Domain Patterns</h2>
          <p className="text-sm text-gray-500 mb-4">
            These patterns appear across multiple domains - your most transferable knowledge.
          </p>
          <div className="flex flex-wrap gap-2">
            {crossDomain.map(pattern => (
              <span
                key={pattern.id}
                className="inline-flex items-center gap-2 bg-purple-100 text-purple-800 px-3 py-2 rounded-lg"
              >
                {pattern.name}
                <span className="text-xs text-purple-600">
                  ({pattern.usage_count} uses)
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Patterns List */}
      <div className="grid grid-cols-2 gap-4">
        {patterns.map(pattern => (
          <div key={pattern.id} className="card hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-semibold text-gray-900">{pattern.name}</h3>
              <span className="badge bg-gray-100 text-gray-600">
                {pattern.usage_count} uses
              </span>
            </div>

            {pattern.description && (
              <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                {pattern.description}
              </p>
            )}

            {pattern.domain_tags && (
              <div className="flex flex-wrap gap-1 mb-3">
                {pattern.domain_tags.split(',').map(tag => (
                  <span key={tag} className={`badge badge-${tag.trim()}`}>
                    {tag.trim()}
                  </span>
                ))}
              </div>
            )}

            {pattern.common_triggers && (
              <div className="text-sm">
                <span className="text-gray-500">Triggers:</span>{' '}
                <span className="text-gray-700">{pattern.common_triggers}</span>
              </div>
            )}

            <div className="mt-3 pt-3 border-t flex items-center justify-between text-sm text-gray-500">
              <span>Success rate: {(pattern.success_rate * 100).toFixed(0)}%</span>
              {pattern.last_used_at && (
                <span>Last used: {new Date(pattern.last_used_at).toLocaleDateString()}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {patterns.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          {search ? 'No patterns found matching your search.' : 'No patterns yet. Create your first pattern!'}
        </div>
      )}

      {/* Create Pattern Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Create New Pattern</h2>
            
            <form onSubmit={handleCreatePattern} className="space-y-4">
              <div>
                <label className="label">Pattern Name *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., sliding window, state compression"
                  value={newPattern.name}
                  onChange={e => setNewPattern(p => ({ ...p, name: e.target.value }))}
                  autoFocus
                />
              </div>

              <div>
                <label className="label">Description</label>
                <textarea
                  className="textarea"
                  placeholder="What does this pattern mean to you?"
                  value={newPattern.description}
                  onChange={e => setNewPattern(p => ({ ...p, description: e.target.value }))}
                />
              </div>

              <div>
                <label className="label">Domain Tags (comma-separated)</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., dsa, backend, ai_ml"
                  value={newPattern.domain_tags}
                  onChange={e => setNewPattern(p => ({ ...p, domain_tags: e.target.value }))}
                />
              </div>

              <div>
                <label className="label">Common Triggers</label>
                <input
                  type="text"
                  className="input"
                  placeholder="What clues suggest this pattern applies?"
                  value={newPattern.common_triggers}
                  onChange={e => setNewPattern(p => ({ ...p, common_triggers: e.target.value }))}
                />
              </div>

              <div>
                <label className="label">Common Mistakes</label>
                <input
                  type="text"
                  className="input"
                  placeholder="What mistakes do you often make with this pattern?"
                  value={newPattern.common_mistakes}
                  onChange={e => setNewPattern(p => ({ ...p, common_mistakes: e.target.value }))}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1">
                  Create Pattern
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
