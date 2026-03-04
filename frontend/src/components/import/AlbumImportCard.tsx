import { useState } from 'react'
import { ConfidenceBadge } from '../shared/ConfidenceBadge'
import { MetadataDiff } from '../shared/MetadataDiff'
import type { WsMessage, AlbumMetadata, TrackInfo } from '../../types'
import styles from './AlbumImportCard.module.css'

interface Props {
  event: WsMessage
}

interface AlbumPayload {
  confidence?: number
  before?: AlbumMetadata
  after?: AlbumMetadata
  artwork?: { found: boolean; source?: string; url?: string }
  tracks?: TrackInfo[]
  album?: string
}

function getStatus(event: WsMessage): 'applied' | 'skipped' | 'waiting' {
  if (event.event === 'album_complete') return 'applied'
  if (event.event === 'album_skipped') return 'skipped'
  return 'waiting'
}

export function AlbumImportCard({ event }: Props) {
  const [tracksExpanded, setTracksExpanded] = useState(false)

  const payload = event.payload as AlbumPayload
  const confidence = typeof payload.confidence === 'number' ? payload.confidence : null
  const before = payload.before ?? {}
  const after = payload.after ?? {}
  const artwork = payload.artwork
  const tracks = payload.tracks ?? []
  const status = getStatus(event)

  const albumTitle =
    String(payload.after?.album ?? payload.before?.album ?? payload.album ?? 'Unknown Album')

  return (
    <div className={`${styles.card} ${styles[status]}`}>
      <div className={styles.header}>
        <span className={styles.albumTitle}>{albumTitle}</span>
        <div className={styles.badges}>
          {confidence !== null && <ConfidenceBadge confidence={confidence} />}
          <span className={`${styles.statusChip} ${styles[`status_${status}`]}`}>
            {status === 'applied' ? 'Applied' : status === 'skipped' ? 'Skipped' : 'Waiting'}
          </span>
          {artwork && (
            <span className={`${styles.artChip} ${artwork.found ? styles.artFound : styles.artMissing}`}>
              {artwork.found ? 'Art ✓' : 'No art'}
            </span>
          )}
        </div>
      </div>

      {(payload.before !== undefined || payload.after !== undefined) && (
        <div className={styles.diff}>
          <MetadataDiff before={before} after={after} />
        </div>
      )}

      {tracks.length > 0 && (
        <div className={styles.tracksSection}>
          <button
            className={styles.tracksToggle}
            onClick={() => setTracksExpanded(p => !p)}
          >
            <span className={`${styles.arrow} ${tracksExpanded ? styles.arrowOpen : ''}`}>▶</span>
            {tracks.length} track{tracks.length !== 1 ? 's' : ''}
          </button>
          {tracksExpanded && (
            <ol className={styles.trackList}>
              {tracks.map((t, i) => (
                <li key={i} className={styles.trackItem}>
                  <span className={styles.trackNum}>{t.track ?? i + 1}</span>
                  <span className={styles.trackTitle}>{t.title}</span>
                  {t.length != null && (
                    <span className={styles.trackLen}>
                      {Math.floor(t.length / 60)}:{String(Math.round(t.length % 60)).padStart(2, '0')}
                    </span>
                  )}
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  )
}
