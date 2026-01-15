import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { 
  ArrowLeft, 
  ExternalLink, 
  Clock, 
  Target,
  Trash2
} from 'lucide-react';
import { entriesApi } from '../lib/api';
import EntryTypeBadge from '../components/EntryTypeBadge';
import ReflectionForm from '../components/ReflectionForm';
import type { EntryWithReflection, ReflectionCreate } from '../lib/types';

export default function EntryDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [entry, setEntry] = useState<EntryWithReflection | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadEntry();
  }, [id]);

  const loadEntry = async () => {
    if (!id) return;
    
    try {
      const data = await entriesApi.get(parseInt(id));
      setEntry(data);
    } catch (err) {
      setError('Failed to load entry');
    } finally {
      setLoading(false);
    }
  };

  const handleReflectionSubmit = async (reflection: ReflectionCreate) => {
    if (!entry) return;

    setSubmitting(true);
    setError('');

    try {
      const updated = await entriesApi.addReflection(entry.id, reflection);
      setEntry(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save reflection');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!entry || !confirm('Are you sure you want to delete this entry?')) return;

    try {
      await entriesApi.delete(entry.id);
      navigate('/');
    } catch (err) {
      setError('Failed to delete entry');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!entry) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-600">Entry not found</h2>
        <Link to="/" className="text-primary-600 hover:underline mt-2 block">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link to="/" className="text-gray-500 hover:text-gray-700 flex items-center gap-1 mb-4">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>

        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <EntryTypeBadge type={entry.entry_type} />
              {entry.difficulty && (
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  <Target className="w-4 h-4" />
                  Difficulty: {entry.difficulty}/5
                </span>
              )}
              {entry.time_spent_minutes && (
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {entry.time_spent_minutes} min
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-gray-900">{entry.title}</h1>
            <p className="text-gray-500 mt-1">
              Created {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
            </p>
          </div>

          <div className="flex gap-2">
            {entry.source_url && (
              <a
                href={entry.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary flex items-center gap-2"
              >
                <ExternalLink className="w-4 h-4" />
                {entry.source_name || 'Source'}
              </a>
            )}
            <button onClick={handleDelete} className="btn-danger flex items-center gap-2">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="col-span-2 space-y-6">
          {/* Code Snippet */}
          {entry.code_snippet && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-3">Code Solution</h2>
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <pre className="text-gray-100 text-sm font-mono whitespace-pre-wrap">
                  {entry.code_snippet}
                </pre>
              </div>
              {entry.language && (
                <p className="text-sm text-gray-500 mt-2">Language: {entry.language}</p>
              )}
            </div>
          )}

          {/* Reflection Section */}
          {entry.is_complete && entry.reflection ? (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">🧠 Reflection</h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Context</h3>
                  <p className="text-gray-800 mt-1">{entry.reflection.context}</p>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-500">Initial Blocker</h3>
                  <p className="text-gray-800 mt-1">{entry.reflection.initial_blocker}</p>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-500">Trigger Signal</h3>
                  <p className="text-gray-800 mt-1">{entry.reflection.trigger_signal}</p>
                </div>

                <div className="bg-primary-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-primary-700">Key Pattern</h3>
                  <p className="text-primary-900 font-semibold mt-1">{entry.reflection.key_pattern}</p>
                </div>

                <div className="bg-red-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-red-700">Mistake / Edge Case</h3>
                  <p className="text-red-900 mt-1">{entry.reflection.mistake_or_edge_case}</p>
                </div>

                {entry.reflection.next_time_strategy && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Next Time Strategy</h3>
                    <p className="text-gray-800 mt-1">{entry.reflection.next_time_strategy}</p>
                  </div>
                )}

                {entry.reflection.additional_notes && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Additional Notes</h3>
                    <p className="text-gray-800 mt-1">{entry.reflection.additional_notes}</p>
                  </div>
                )}

                <div className="flex items-center gap-4 pt-4 border-t">
                  {entry.reflection.confidence_level && (
                    <span className="text-sm text-gray-500">
                      Confidence: {entry.reflection.confidence_level}/5
                    </span>
                  )}
                  {entry.reflection.time_to_insight_minutes && (
                    <span className="text-sm text-gray-500">
                      Time to insight: {entry.reflection.time_to_insight_minutes} min
                    </span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Add Reflection</h2>
              <ReflectionForm
                onSubmit={handleReflectionSubmit}
                isSubmitting={submitting}
              />
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status Card */}
          <div className={`card ${entry.is_complete ? 'bg-green-50' : 'bg-yellow-50'}`}>
            <h3 className="font-semibold mb-2">
              {entry.is_complete ? '✅ Complete' : '⚠️ Incomplete'}
            </h3>
            <p className="text-sm text-gray-600">
              {entry.is_complete
                ? 'This entry has been completed with reflection.'
                : 'Add a reflection to complete this entry.'}
            </p>
          </div>

          {/* Patterns */}
          {entry.patterns.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3">🏷️ Patterns</h3>
              <div className="space-y-2">
                {entry.patterns.map(pattern => (
                  <Link
                    key={pattern.id}
                    to={`/patterns?id=${pattern.id}`}
                    className="block bg-gray-50 p-3 rounded-lg hover:bg-gray-100"
                  >
                    <p className="font-medium">{pattern.name}</p>
                    {pattern.description && (
                      <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                        {pattern.description}
                      </p>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="card">
            <h3 className="font-semibold mb-3">📋 Details</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Domain</dt>
                <dd className="font-medium capitalize">{entry.entry_type.replace('_', '/')}</dd>
              </div>
              {entry.source_name && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Source</dt>
                  <dd className="font-medium">{entry.source_name}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd className="font-medium">
                  {new Date(entry.created_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
