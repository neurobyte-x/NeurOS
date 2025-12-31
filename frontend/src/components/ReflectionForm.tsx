import { useState, useEffect } from 'react';
import type { ReflectionCreate } from '../lib/types';

interface ReflectionFormProps {
  onSubmit: (reflection: ReflectionCreate) => void;
  isSubmitting: boolean;
  initialData?: Partial<ReflectionCreate>;
}

/**
 * The reflection form is THE key component of Thinking OS.
 * 
 * WHY: This enforces the "reflection before persistence" philosophy.
 * All fields are mandatory and validated to ensure quality reflection.
 */
export default function ReflectionForm({ 
  onSubmit, 
  isSubmitting,
  initialData 
}: ReflectionFormProps) {
  const [formData, setFormData] = useState<ReflectionCreate>({
    context: initialData?.context || '',
    initial_blocker: initialData?.initial_blocker || '',
    trigger_signal: initialData?.trigger_signal || '',
    key_pattern: initialData?.key_pattern || '',
    mistake_or_edge_case: initialData?.mistake_or_edge_case || '',
    time_to_insight_minutes: initialData?.time_to_insight_minutes,
    additional_notes: initialData?.additional_notes || '',
    next_time_strategy: initialData?.next_time_strategy || '',
    confidence_level: initialData?.confidence_level || 3,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.context || formData.context.length < 10) {
      newErrors.context = 'Context must be at least 10 characters';
    }
    if (!formData.initial_blocker || formData.initial_blocker.length < 10) {
      newErrors.initial_blocker = 'Initial blocker must be at least 10 characters';
    }
    if (!formData.trigger_signal || formData.trigger_signal.length < 5) {
      newErrors.trigger_signal = 'Trigger signal must be at least 5 characters';
    }
    if (!formData.key_pattern || formData.key_pattern.length < 3) {
      newErrors.key_pattern = 'Key pattern must be at least 3 characters';
    }
    if (!formData.mistake_or_edge_case || formData.mistake_or_edge_case.length < 5) {
      newErrors.mistake_or_edge_case = 'Mistake/edge case must be at least 5 characters';
    }
    if (formData.context === formData.initial_blocker) {
      newErrors.initial_blocker = 'Context and blocker should be different';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  const handleChange = (
    field: keyof ReflectionCreate,
    value: string | number | undefined
  ) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-yellow-800 mb-2">
          🧠 Reflection Required
        </h3>
        <p className="text-sm text-yellow-700">
          This is where learning happens. Take time to reflect on your thinking process.
          All fields marked with * are required.
        </p>
      </div>

      {/* Context */}
      <div>
        <label className="label">
          Context * <span className="text-gray-400 font-normal">(What were you trying to solve/build?)</span>
        </label>
        <textarea
          className={`textarea h-24 ${errors.context ? 'border-red-500' : ''}`}
          placeholder="Describe the problem or task you were working on..."
          value={formData.context}
          onChange={e => handleChange('context', e.target.value)}
        />
        {errors.context && (
          <p className="text-red-500 text-sm mt-1">{errors.context}</p>
        )}
      </div>

      {/* Initial Blocker */}
      <div>
        <label className="label">
          Initial Blocker * <span className="text-gray-400 font-normal">(Why were you stuck or unsure?)</span>
        </label>
        <textarea
          className={`textarea h-24 ${errors.initial_blocker ? 'border-red-500' : ''}`}
          placeholder="What was preventing you from solving it? What gap in knowledge or understanding did you face?"
          value={formData.initial_blocker}
          onChange={e => handleChange('initial_blocker', e.target.value)}
        />
        {errors.initial_blocker && (
          <p className="text-red-500 text-sm mt-1">{errors.initial_blocker}</p>
        )}
      </div>

      {/* Trigger Signal */}
      <div>
        <label className="label">
          Trigger Signal * <span className="text-gray-400 font-normal">(What revealed the correct direction?)</span>
        </label>
        <textarea
          className={`textarea h-20 ${errors.trigger_signal ? 'border-red-500' : ''}`}
          placeholder="What hint, error message, or insight pointed you to the solution?"
          value={formData.trigger_signal}
          onChange={e => handleChange('trigger_signal', e.target.value)}
        />
        {errors.trigger_signal && (
          <p className="text-red-500 text-sm mt-1">{errors.trigger_signal}</p>
        )}
      </div>

      {/* Key Pattern */}
      <div>
        <label className="label">
          Key Pattern * <span className="text-gray-400 font-normal">(Name it in YOUR words)</span>
        </label>
        <input
          type="text"
          className={`input ${errors.key_pattern ? 'border-red-500' : ''}`}
          placeholder="e.g., 'sliding window', 'state compression', 'bottleneck identification'"
          value={formData.key_pattern}
          onChange={e => handleChange('key_pattern', e.target.value)}
        />
        {errors.key_pattern && (
          <p className="text-red-500 text-sm mt-1">{errors.key_pattern}</p>
        )}
        <p className="text-xs text-gray-500 mt-1">
          Use your own terminology. This builds your personal pattern vocabulary.
        </p>
      </div>

      {/* Mistake or Edge Case */}
      <div>
        <label className="label">
          Mistake or Edge Case * <span className="text-gray-400 font-normal">(One thing to remember)</span>
        </label>
        <textarea
          className={`textarea h-20 ${errors.mistake_or_edge_case ? 'border-red-500' : ''}`}
          placeholder="What specific mistake did you make? What edge case almost caught you?"
          value={formData.mistake_or_edge_case}
          onChange={e => handleChange('mistake_or_edge_case', e.target.value)}
        />
        {errors.mistake_or_edge_case && (
          <p className="text-red-500 text-sm mt-1">{errors.mistake_or_edge_case}</p>
        )}
      </div>

      <hr className="my-6" />

      {/* Optional Fields */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Time to Insight (minutes)</label>
          <input
            type="number"
            className="input"
            placeholder="How long until breakthrough?"
            value={formData.time_to_insight_minutes || ''}
            onChange={e => handleChange('time_to_insight_minutes', e.target.value ? parseInt(e.target.value) : undefined)}
            min={0}
          />
        </div>

        <div>
          <label className="label">Confidence Level (1-5)</label>
          <select
            className="input"
            value={formData.confidence_level || 3}
            onChange={e => handleChange('confidence_level', parseInt(e.target.value))}
          >
            <option value={1}>1 - Still shaky</option>
            <option value={2}>2 - Somewhat unsure</option>
            <option value={3}>3 - Moderately confident</option>
            <option value={4}>4 - Pretty confident</option>
            <option value={5}>5 - Fully understood</option>
          </select>
        </div>
      </div>

      <div>
        <label className="label">Next Time Strategy</label>
        <textarea
          className="textarea h-20"
          placeholder="What would you do differently next time?"
          value={formData.next_time_strategy}
          onChange={e => handleChange('next_time_strategy', e.target.value)}
        />
      </div>

      <div>
        <label className="label">Additional Notes</label>
        <textarea
          className="textarea h-20"
          placeholder="Any other thoughts or observations..."
          value={formData.additional_notes}
          onChange={e => handleChange('additional_notes', e.target.value)}
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="btn-primary w-full py-3 text-lg"
      >
        {isSubmitting ? 'Saving...' : '✨ Complete Entry with Reflection'}
      </button>
    </form>
  );
}
