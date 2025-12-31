import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { CheckCircle, AlertCircle, ExternalLink } from 'lucide-react';
import EntryTypeBadge from './EntryTypeBadge';
import type { Entry } from '../lib/types';

interface EntryCardProps {
  entry: Entry;
}

export default function EntryCard({ entry }: EntryCardProps) {
  return (
    <Link
      to={`/entry/${entry.id}`}
      className="card hover:shadow-md transition-shadow block"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <EntryTypeBadge type={entry.entry_type} size="sm" />
          {entry.difficulty && (
            <span className="text-xs text-gray-500">
              Difficulty: {entry.difficulty}/5
            </span>
          )}
        </div>
        {entry.is_complete ? (
          <CheckCircle className="w-5 h-5 text-green-500" />
        ) : (
          <AlertCircle className="w-5 h-5 text-yellow-500" />
        )}
      </div>

      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
        {entry.title}
      </h3>

      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>
          {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
        </span>
        
        <div className="flex items-center gap-3">
          {entry.time_spent_minutes && (
            <span>{entry.time_spent_minutes} min</span>
          )}
          {entry.source_url && (
            <ExternalLink className="w-4 h-4" />
          )}
        </div>
      </div>

      {!entry.is_complete && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <span className="text-sm text-yellow-600 font-medium">
            ⚠️ Needs reflection to complete
          </span>
        </div>
      )}
    </Link>
  );
}
