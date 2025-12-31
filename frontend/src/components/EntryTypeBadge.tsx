import { ENTRY_TYPES, type EntryType } from '../lib/types';

interface EntryTypeBadgeProps {
  type: EntryType;
  size?: 'sm' | 'md';
}

export default function EntryTypeBadge({ type, size = 'md' }: EntryTypeBadgeProps) {
  const typeInfo = ENTRY_TYPES.find(t => t.value === type);
  
  if (!typeInfo) return null;

  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1';

  return (
    <span className={`badge badge-${type} ${sizeClasses}`}>
      {typeInfo.label}
    </span>
  );
}
