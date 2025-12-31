import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Lightbulb, AlertTriangle, Target, BookOpen } from 'lucide-react';
import { recallApi } from '../lib/api';
import { ENTRY_TYPES, type RecallResponse, type EntryType } from '../lib/types';

/**
 * Recall page - the intelligence interface.
 * 
 * WHY: Before starting new work, check what you already know.
 * This surfaces similar entries, relevant patterns, and warnings.
 */
export default function Recall() {
  const [title, setTitle] = useState('');
  const [entryType, setEntryType] = useState<EntryType | ''>('');
  const [keywords, setKeywords] = useState('');
  const [result, setResult] = useState<RecallResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() && !keywords.trim()) return;

    setLoading(true);
    try {
      const data = await recallApi.getContext({
        title: title || undefined,
        entry_type: entryType || undefined,
        keywords: keywords ? keywords.split(',').map(k => k.trim()) : undefined,
      });
      setResult(data);
    } catch (error) {
      console.error('Failed to get recall:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Recall</h1>
        <p className="text-gray-500 mt-1">
          Search your past experiences before starting new work
        </p>
      </div>

      {/* Search Form */}
      <div className="card">
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label className="label">What are you working on?</label>
            <input
              type="text"
              className="input"
              placeholder="e.g., Binary search with duplicate elements"
              value={title}
              onChange={e => setTitle(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Domain (optional)</label>
              <select
                className="input"
                value={entryType}
                onChange={e => setEntryType(e.target.value as EntryType | '')}
              >
                <option value="">All domains</option>
                {ENTRY_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Keywords (comma-separated)</label>
              <input
                type="text"
                className="input"
                placeholder="e.g., binary search, off by one"
                value={keywords}
                onChange={e => setKeywords(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || (!title.trim() && !keywords.trim())}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Search My Memory
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6 animate-fadeIn">
          {/* Similar Entries */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5 text-blue-500" />
              <h2 className="text-lg font-semibold">Similar Past Entries</h2>
            </div>

            {result.similar_entries.length > 0 ? (
              <div className="space-y-3">
                {result.similar_entries.map(entry => (
                  <Link
                    key={entry.entry_id}
                    to={`/entry/${entry.entry_id}`}
                    className="block bg-blue-50 hover:bg-blue-100 p-4 rounded-lg transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{entry.entry_title}</h3>
                        <p className="text-sm text-gray-600 mt-1">
                          {entry.similarity_reason}
                        </p>
                      </div>
                      <span className="text-sm text-gray-500">
                        {entry.days_ago} days ago
                      </span>
                    </div>
                    {entry.key_pattern && (
                      <div className="mt-2">
                        <span className="badge bg-blue-200 text-blue-800">
                          Pattern: {entry.key_pattern}
                        </span>
                      </div>
                    )}
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">
                No similar entries found. This looks like new territory!
              </p>
            )}
          </div>

          {/* Relevant Patterns */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-5 h-5 text-purple-500" />
              <h2 className="text-lg font-semibold">Relevant Patterns</h2>
            </div>

            {result.relevant_patterns.length > 0 ? (
              <div className="space-y-3">
                {result.relevant_patterns.map(pattern => (
                  <div
                    key={pattern.pattern_id}
                    className="bg-purple-50 p-4 rounded-lg"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{pattern.pattern_name}</h3>
                        {pattern.description && (
                          <p className="text-sm text-gray-600 mt-1">{pattern.description}</p>
                        )}
                      </div>
                      <span className="text-sm text-purple-600">
                        {pattern.usage_count} uses • {(pattern.success_rate * 100).toFixed(0)}% success
                      </span>
                    </div>
                    {pattern.common_triggers && (
                      <p className="text-sm text-gray-500 mt-2">
                        <strong>Triggers:</strong> {pattern.common_triggers}
                      </p>
                    )}
                    {pattern.common_mistakes && (
                      <p className="text-sm text-red-600 mt-1">
                        <strong>Watch out:</strong> {pattern.common_mistakes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">
                No relevant patterns found.
              </p>
            )}
          </div>

          {/* Blocker Warnings */}
          {result.blocker_warnings.length > 0 && (
            <div className="card bg-yellow-50 border-yellow-200">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                <h2 className="text-lg font-semibold text-yellow-800">Watch Out For</h2>
              </div>

              <div className="space-y-2">
                {result.blocker_warnings.map((warning, i) => (
                  <div key={i} className="bg-white p-3 rounded-lg text-sm text-yellow-800">
                    {warning}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Revision Suggestions */}
          {result.revision_suggestions.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="w-5 h-5 text-orange-500" />
                <h2 className="text-lg font-semibold">Suggested Revisions</h2>
              </div>

              <div className="space-y-3">
                {result.revision_suggestions.map((suggestion, i) => (
                  <div key={i} className="bg-orange-50 p-4 rounded-lg">
                    <h3 className="font-medium text-gray-900">{suggestion.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{suggestion.description}</p>
                    <p className="text-sm text-orange-600 mt-2">
                      💡 {suggestion.action_text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && (
        <div className="text-center py-12 text-gray-500">
          <Lightbulb className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium">Search your memory</h3>
          <p className="mt-1">
            Enter what you're working on to find relevant past experiences
          </p>
        </div>
      )}
    </div>
  );
}
