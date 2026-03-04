interface Props {
  confidence: number  // 0–1
}

export function ConfidenceBadge({ confidence }: Props) {
  const pct = Math.round(confidence * 100)
  const color = pct >= 90 ? '#22c55e' : pct >= 70 ? '#f59e0b' : '#ef4444'
  return (
    <span style={{
      background: color,
      color: '#fff',
      borderRadius: '4px',
      padding: '2px 8px',
      fontSize: '0.75rem',
      fontWeight: 600,
    }}>
      {pct}%
    </span>
  )
}
