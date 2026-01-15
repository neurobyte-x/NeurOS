import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, Edit3, Lightbulb, AlertCircle, Check } from 'lucide-react';
import { entriesApi, recallApi, aiApi } from '../lib/api';
import { ENTRY_TYPES, type EntryCreate, type RecallResponse } from '../lib/types';

type Step = 'describe' | 'analyzing' | 'review' | 'recall' | 'creating';

export default function NewEntry() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('describe');
  const [aiEnabled, setAiEnabled] = useState(false);
  const [rawInput, setRawInput] = useState('');
  const [formData, setFormData] = useState<EntryCreate>({
    title: '',
    entry_type: 'dsa',
    source_url: '',
    source_name: '',
    difficulty: undefined,
    time_spent_minutes: undefined,
    code_snippet: '',
    language: '',
  });
  const [reflectionData, setReflectionData] = useState({
    context: '',
    initial_blocker: '',
    trigger_signal: '',
    key_pattern: '',
    mistake_or_edge_case: '',
  });
  const [suggestedPatterns, setSuggestedPatterns] = useState<string[]>([]);
  const [recallData, setRecallData] = useState<RecallResponse | null>(null);
  const [error, setError] = useState('');

  // Check if AI is enabled
  useEffect(() => {
    aiApi.status().then(status => setAiEnabled(status.configured)).catch(() => setAiEnabled(false));
  }, []);

  const analyzeExperience = async () => {
    if (rawInput.trim().length < 50) {
      setError('Please describe your experience in more detail (at least 50 characters)');
      return;
    }

    setStep('analyzing');
    setError('');

    try {
      const result = await aiApi.analyze(rawInput);
      
      // Populate form data
      setFormData(prev => ({
        ...prev,
        title: result.title,
        entry_type: result.entry_type as any,
        difficulty: result.difficulty,
        time_spent_minutes: result.time_spent_minutes,
      }));

      // Populate reflection data
      setReflectionData({
        context: result.context,
        initial_blocker: result.initial_blocker,
        trigger_signal: result.trigger_signal,
        key_pattern: result.key_pattern,
        mistake_or_edge_case: result.mistake_or_edge_case,
      });

      setSuggestedPatterns(result.suggested_patterns);
      setStep('review');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'AI analysis failed. Please try again.');
      setStep('describe');
    }
  };

  const handleFormChange = (field: keyof EntryCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleReflectionChange = (field: string, value: string) => {
    setReflectionData(prev => ({ ...prev, [field]: value }));
  };

  const fetchRecall = async () => {
    setStep('recall');
    try {
      const recall = await recallApi.getContext({
        title: formData.title,
        entry_type: formData.entry_type,
      });
      setRecallData(recall);
    } catch (err) {
      console.error('Failed to fetch recall:', err);
    }
  };

  const createEntry = async () => {
    setStep('creating');
    setError('');

    try {
      // Create entry
      const entry = await entriesApi.create(formData);
      
      // Add reflection immediately
      await entriesApi.addReflection(entry.id, {
        ...reflectionData,
      });

      navigate(`/entry/${entry.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create entry');
      setStep('review');
    }
  };

  // Describe step - conversational input
  if (step === 'describe') {
    return (
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">What did you learn today?</h1>
        <p className="text-gray-500 mb-8">
          Just describe your experience — the problem, where you got stuck, how you solved it.
          {aiEnabled ? " AI will extract the structured data for you." : ""}
        </p>

        {!aiEnabled && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <p className="font-medium text-yellow-800">AI not configured</p>
              <p className="text-sm text-yellow-700">
                Set GEMINI_API_KEY in backend/.env to enable AI-powered analysis.
              </p>
            </div>
          </div>
        )}

        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-purple-500" />
            <span className="text-sm font-medium text-purple-600">AI-Powered Entry Creation</span>
          </div>

          <textarea
            className="textarea h-64 mb-4"
            placeholder={`Tell me about your learning experience. For example:

"Spent about 2 hours trying to solve the two-sum problem on LeetCode. I was stuck because I kept using nested loops which was timing out on large inputs. The breakthrough came when I realized I could use a hash map to store numbers I've already seen and check if the complement exists in O(1). The key pattern here is: when looking for pairs in an array, hash maps turn O(n²) into O(n). Watch out for the edge case where the same element can't be used twice."

Include:
• What you were trying to do
• Where you got stuck
• How long it took
• What helped you break through
• What you'll remember for next time`}
            value={rawInput}
            onChange={e => setRawInput(e.target.value)}
            autoFocus
          />

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">
              {rawInput.length}/50 characters minimum
            </span>
            
            {error && (
              <span className="text-sm text-red-600">{error}</span>
            )}
          </div>

          <button
            onClick={analyzeExperience}
            disabled={!aiEnabled || rawInput.length < 50}
            className="btn-primary w-full mt-4 py-3 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Sparkles className="w-5 h-5" />
            Analyze with AI
          </button>
        </div>
      </div>
    );
  }

  // Analyzing step
  if (step === 'analyzing') {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="card text-center py-16">
          <div className="relative mx-auto w-16 h-16 mb-6">
            <div className="absolute inset-0 rounded-full border-4 border-purple-100"></div>
            <div className="absolute inset-0 rounded-full border-4 border-purple-500 border-t-transparent animate-spin"></div>
            <Sparkles className="absolute inset-0 m-auto w-6 h-6 text-purple-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Analyzing your experience...</h2>
          <p className="text-gray-500">AI is extracting structured learning data</p>
        </div>
      </div>
    );
  }

  // Review step - edit extracted data
  if (step === 'review') {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Review & Edit</h1>
            <p className="text-gray-500">AI extracted these fields. Edit anything that needs adjustment.</p>
          </div>
          <div className="flex items-center gap-2 text-green-600 bg-green-50 px-3 py-1 rounded-full">
            <Check className="w-4 h-4" />
            <span className="text-sm font-medium">Analysis complete</span>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-6">{error}</div>
        )}

        <div className="grid grid-cols-2 gap-6">
          {/* Left column - Entry details */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Edit3 className="w-5 h-5" />
              Entry Details
            </h2>

            <div className="space-y-4">
              <div>
                <label className="label">Title</label>
                <input
                  type="text"
                  className="input"
                  value={formData.title}
                  onChange={e => handleFormChange('title', e.target.value)}
                />
              </div>

              <div>
                <label className="label">Domain</label>
                <div className="grid grid-cols-4 gap-2">
                  {ENTRY_TYPES.map(type => (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => handleFormChange('entry_type', type.value)}
                      className={`p-2 rounded-lg border-2 transition-colors text-xs ${
                        formData.entry_type === type.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {type.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Difficulty</label>
                  <select
                    className="input"
                    value={formData.difficulty || ''}
                    onChange={e => handleFormChange('difficulty', e.target.value ? parseInt(e.target.value) : undefined)}
                  >
                    <option value="">Select...</option>
                    <option value="1">1 - Easy</option>
                    <option value="2">2 - Medium-Easy</option>
                    <option value="3">3 - Medium</option>
                    <option value="4">4 - Medium-Hard</option>
                    <option value="5">5 - Hard</option>
                  </select>
                </div>
                <div>
                  <label className="label">Time (min)</label>
                  <input
                    type="number"
                    className="input"
                    value={formData.time_spent_minutes || ''}
                    onChange={e => handleFormChange('time_spent_minutes', e.target.value ? parseInt(e.target.value) : undefined)}
                    min={0}
                  />
                </div>
              </div>

              {suggestedPatterns.length > 0 && (
                <div>
                  <label className="label">Suggested Patterns</label>
                  <div className="flex flex-wrap gap-2">
                    {suggestedPatterns.map((pattern, i) => (
                      <span key={i} className="badge bg-purple-100 text-purple-800">
                        {pattern}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right column - Reflection */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-yellow-500" />
              Reflection (AI Extracted)
            </h2>

            <div className="space-y-4">
              <div>
                <label className="label">Context</label>
                <textarea
                  className="textarea h-16 text-sm"
                  value={reflectionData.context}
                  onChange={e => handleReflectionChange('context', e.target.value)}
                />
              </div>

              <div>
                <label className="label">Initial Blocker</label>
                <textarea
                  className="textarea h-16 text-sm"
                  value={reflectionData.initial_blocker}
                  onChange={e => handleReflectionChange('initial_blocker', e.target.value)}
                />
              </div>

              <div>
                <label className="label">Trigger Signal (Aha Moment)</label>
                <textarea
                  className="textarea h-16 text-sm"
                  value={reflectionData.trigger_signal}
                  onChange={e => handleReflectionChange('trigger_signal', e.target.value)}
                />
              </div>

              <div>
                <label className="label">Key Pattern</label>
                <textarea
                  className="textarea h-16 text-sm"
                  value={reflectionData.key_pattern}
                  onChange={e => handleReflectionChange('key_pattern', e.target.value)}
                />
              </div>

              <div>
                <label className="label">Edge Case / Mistake</label>
                <textarea
                  className="textarea h-16 text-sm"
                  value={reflectionData.mistake_or_edge_case}
                  onChange={e => handleReflectionChange('mistake_or_edge_case', e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-4 mt-6">
          <button
            onClick={() => setStep('describe')}
            className="btn-secondary flex-1"
          >
            ← Back to Description
          </button>
          <button
            onClick={fetchRecall}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            Check Similar Entries
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  }

  // Recall step
  if (step === 'recall') {
    return (
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Before You Save...</h1>

        <div className="card mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            <h2 className="text-lg font-semibold">Related Insights</h2>
          </div>

          {recallData ? (
            <div className="space-y-6">
              {recallData.similar_entries.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">📚 Similar Past Entries</h3>
                  <div className="space-y-2">
                    {recallData.similar_entries.map(entry => (
                      <div key={entry.entry_id} className="bg-blue-50 p-3 rounded-lg">
                        <p className="font-medium">{entry.entry_title}</p>
                        <p className="text-sm text-gray-600">
                          Pattern: {entry.key_pattern || 'N/A'} • {entry.days_ago} days ago
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {recallData.relevant_patterns.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">🎯 Relevant Patterns</h3>
                  <div className="flex flex-wrap gap-2">
                    {recallData.relevant_patterns.map(pattern => (
                      <span key={pattern.pattern_id} className="badge bg-purple-100 text-purple-800">
                        {pattern.pattern_name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {recallData.blocker_warnings.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">⚠️ Watch Out For</h3>
                  <div className="space-y-2">
                    {recallData.blocker_warnings.map((warning, i) => (
                      <div key={i} className="bg-yellow-50 p-3 rounded-lg text-sm">
                        {warning}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {recallData.similar_entries.length === 0 && 
               recallData.relevant_patterns.length === 0 && 
               recallData.blocker_warnings.length === 0 && (
                <p className="text-gray-500 text-center py-4">
                  No similar entries found. This looks like new territory! 🚀
                </p>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
              <p className="text-gray-500">Loading recall context...</p>
            </div>
          )}
        </div>

        <div className="flex gap-4">
          <button
            onClick={() => setStep('review')}
            className="btn-secondary flex-1"
          >
            ← Back to Edit
          </button>
          <button
            onClick={createEntry}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            <Check className="w-5 h-5" />
            Save Entry with Reflection
          </button>
        </div>
      </div>
    );
  }

  // Creating step
  return (
    <div className="max-w-3xl mx-auto">
      <div className="card text-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Creating your entry...</p>
      </div>
    </div>
  );
}
