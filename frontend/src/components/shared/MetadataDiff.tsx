import type { AlbumMetadata } from '../../types'

interface Props {
  before: AlbumMetadata
  after: AlbumMetadata
}

const FIELDS: (keyof AlbumMetadata)[] = ['artist', 'album', 'albumartist', 'year', 'genre']

export function MetadataDiff({ before, after }: Props) {
  return (
    <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.82rem' }}>
      <thead>
        <tr>
          <th style={th}>Field</th>
          <th style={th}>Before</th>
          <th style={th}>After</th>
        </tr>
      </thead>
      <tbody>
        {FIELDS.map(f => {
          const changed = String(before[f] ?? '') !== String(after[f] ?? '')
          return (
            <tr key={f} style={{ background: changed ? '#1e1e2e' : 'transparent' }}>
              <td style={td}>{f}</td>
              <td style={{ ...td, color: changed ? '#f87171' : '#94a3b8' }}>{String(before[f] ?? '—')}</td>
              <td style={{ ...td, color: changed ? '#4ade80' : '#94a3b8' }}>{String(after[f] ?? '—')}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

const th: React.CSSProperties = {
  textAlign: 'left',
  padding: '4px 8px',
  color: '#64748b',
  fontWeight: 500,
  borderBottom: '1px solid #2d2d44',
}

const td: React.CSSProperties = {
  padding: '3px 8px',
  color: '#94a3b8',
}
