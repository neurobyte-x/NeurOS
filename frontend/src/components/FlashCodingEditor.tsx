/**
 * NeurOS 2.0 Flash Coding Editor Component
 * Uses Monaco Editor for interactive code challenges
 */

import { useState, useCallback } from 'react';
import Editor, { type OnMount } from '@monaco-editor/react';
import type { PatternTemplate, ReviewItemWithData, ReviewSubmit } from '../lib/types';

interface FlashCodingEditorProps {
  reviewItem: ReviewItemWithData;
  template?: PatternTemplate;
  onSubmit: (data: ReviewSubmit) => void;
  isSubmitting: boolean;
}

const LANGUAGE_MAP: Record<string, string> = {
  python: 'python',
  javascript: 'javascript',
  typescript: 'typescript',
  rust: 'rust',
  go: 'go',
  java: 'java',
  cpp: 'cpp',
  c: 'c',
  csharp: 'csharp',
  ruby: 'ruby',
  swift: 'swift',
  kotlin: 'kotlin',
  sql: 'sql',
  bash: 'shell',
  other: 'plaintext',
};

export function FlashCodingEditor({
  reviewItem,
  template,
  onSubmit,
  isSubmitting,
}: FlashCodingEditorProps) {
  const [code, setCode] = useState(template?.template_code || '// Write your solution here\n');
  const [showHint, setShowHint] = useState(false);
  const [showSolution, setShowSolution] = useState(false);
  const [startTime] = useState(Date.now());
  const [selfAssessment, setSelfAssessment] = useState<number | null>(null);

  const language = template ? LANGUAGE_MAP[template.language] : 'javascript';

  const handleEditorMount: OnMount = (editor) => {
    editor.focus();
  };

  const handleSubmitReview = useCallback(
    (quality: number) => {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      onSubmit({
        quality,
        time_spent_seconds: timeSpent,
        notes: code,
      });
    },
    [code, startTime, onSubmit]
  );

  const qualityButtons = [
    { quality: 0, label: 'Blackout', color: 'bg-red-600', desc: "Couldn't recall at all" },
    { quality: 1, label: 'Wrong', color: 'bg-red-500', desc: 'Incorrect response' },
    { quality: 2, label: 'Hard', color: 'bg-orange-500', desc: 'Correct with difficulty' },
    { quality: 3, label: 'Good', color: 'bg-yellow-500', desc: 'Correct with hesitation' },
    { quality: 4, label: 'Easy', color: 'bg-green-500', desc: 'Correct with ease' },
    { quality: 5, label: 'Perfect', color: 'bg-green-600', desc: 'Instant recall' },
  ];

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-gray-800 border-b border-gray-700">
        <h2 className="text-xl font-bold text-white mb-2">
          {reviewItem.item_data?.title || 'Flash Coding Challenge'}
        </h2>
        <p className="text-gray-300 text-sm">
          {reviewItem.item_data?.content || 'Implement the pattern from memory'}
        </p>
        {template && (
          <div className="mt-2 flex gap-2">
            <span className="px-2 py-1 bg-blue-600 text-xs rounded text-white">
              {template.language}
            </span>
            {template.time_complexity && (
              <span className="px-2 py-1 bg-purple-600 text-xs rounded text-white">
                Time: {template.time_complexity}
              </span>
            )}
            {template.space_complexity && (
              <span className="px-2 py-1 bg-indigo-600 text-xs rounded text-white">
                Space: {template.space_complexity}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Editor */}
      <div className="flex-1 min-h-[300px]">
        <Editor
          height="100%"
          language={language}
          value={code}
          onChange={(value) => setCode(value || '')}
          onMount={handleEditorMount}
          theme="vs-dark"
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            wordWrap: 'on',
          }}
        />
      </div>

      {/* Hint & Solution */}
      <div className="p-4 bg-gray-800 border-t border-gray-700">
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setShowHint(!showHint)}
            className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white text-sm rounded transition"
          >
            {showHint ? 'Hide Hint' : 'Show Hint'}
          </button>
          <button
            onClick={() => setShowSolution(!showSolution)}
            className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded transition"
          >
            {showSolution ? 'Hide Solution' : 'Show Solution'}
          </button>
        </div>

        {showHint && template?.when_to_use && (
          <div className="mb-4 p-3 bg-yellow-900/30 border border-yellow-700 rounded">
            <h4 className="text-yellow-400 font-semibold mb-1">When to use:</h4>
            <p className="text-yellow-200 text-sm">{template.when_to_use}</p>
            {template.edge_cases && template.edge_cases.length > 0 && (
              <>
                <h4 className="text-yellow-400 font-semibold mt-2 mb-1">Edge cases:</h4>
                <ul className="list-disc list-inside text-yellow-200 text-sm">
                  {template.edge_cases.map((ec, i) => (
                    <li key={i}>{ec}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        {showSolution && template?.template_code && (
          <div className="mb-4 p-3 bg-green-900/30 border border-green-700 rounded">
            <h4 className="text-green-400 font-semibold mb-2">Solution:</h4>
            <pre className="text-green-200 text-sm overflow-x-auto whitespace-pre-wrap">
              {template.template_code}
            </pre>
          </div>
        )}

        {/* Self Assessment */}
        <div>
          <h4 className="text-white font-semibold mb-2">How did you do?</h4>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
            {qualityButtons.map(({ quality, label, color, desc }) => (
              <button
                key={quality}
                onClick={() => {
                  setSelfAssessment(quality);
                  handleSubmitReview(quality);
                }}
                disabled={isSubmitting}
                className={`
                  ${color} hover:opacity-90 text-white py-2 px-3 rounded 
                  transition flex flex-col items-center
                  ${selfAssessment === quality ? 'ring-2 ring-white' : ''}
                  ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                <span className="font-bold">{label}</span>
                <span className="text-xs opacity-80">{desc}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default FlashCodingEditor;
