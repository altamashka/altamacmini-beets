interface Props {
  value: number  // 0–100
  label?: string
}

export function ProgressBar({ value, label }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {label && <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{label}</span>}
      <div style={{ height: 6, background: '#2d2d44', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${Math.min(100, Math.max(0, value))}%`,
          background: '#a78bfa',
          borderRadius: 3,
          transition: 'width 0.3s ease',
        }} />
      </div>
    </div>
  )
}
