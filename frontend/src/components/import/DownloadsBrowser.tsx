import { useEffect, useState } from 'react'
import { browseDownloads } from '../../api'
import type { DownloadEntry } from '../../types'
import styles from './DownloadsBrowser.module.css'

interface Props {
  onSelectionChange: (paths: string[]) => void
}

interface ArtistNode {
  entry: DownloadEntry
  expanded: boolean
  albums: DownloadEntry[]
  loading: boolean
}

export function DownloadsBrowser({ onSelectionChange }: Props) {
  const [artists, setArtists] = useState<ArtistNode[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [rootLoading, setRootLoading] = useState(true)
  const [rootError, setRootError] = useState<string | null>(null)

  useEffect(() => {
    setRootLoading(true)
    browseDownloads()
      .then(result => {
        const dirs = result.entries.filter(e => e.is_dir)
        setArtists(dirs.map(e => ({ entry: e, expanded: false, albums: [], loading: false })))
        setRootError(null)
      })
      .catch(() => setRootError('Failed to load downloads'))
      .finally(() => setRootLoading(false))
  }, [])

  useEffect(() => {
    onSelectionChange(Array.from(selected))
  }, [selected, onSelectionChange])

  function toggleExpand(idx: number) {
    const node = artists[idx]
    if (node.expanded) {
      setArtists(prev => prev.map((a, i) => i === idx ? { ...a, expanded: false } : a))
      return
    }
    if (node.albums.length > 0) {
      setArtists(prev => prev.map((a, i) => i === idx ? { ...a, expanded: true } : a))
      return
    }
    setArtists(prev => prev.map((a, i) => i === idx ? { ...a, loading: true } : a))
    browseDownloads(node.entry.path)
      .then(result => {
        const dirs = result.entries.filter(e => e.is_dir)
        setArtists(prev => prev.map((a, i) =>
          i === idx ? { ...a, expanded: true, albums: dirs, loading: false } : a
        ))
      })
      .catch(() => {
        setArtists(prev => prev.map((a, i) =>
          i === idx ? { ...a, loading: false } : a
        ))
      })
  }

  function toggleAlbumSelect(path: string) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }

  function toggleArtistSelect(artist: ArtistNode) {
    const artistPath = artist.entry.path
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(artistPath)) {
        next.delete(artistPath)
        artist.albums.forEach(a => next.delete(a.path))
      } else {
        next.add(artistPath)
      }
      return next
    })
  }

  if (rootLoading) {
    return <div className={styles.loading}>Loading downloads…</div>
  }

  if (rootError) {
    return <div className={styles.error}>{rootError}</div>
  }

  if (artists.length === 0) {
    return <div className={styles.empty}>No folders found in downloads.</div>
  }

  return (
    <div className={styles.tree}>
      {artists.map((node, idx) => (
        <div key={node.entry.path} className={styles.artistGroup}>
          <div className={styles.artistRow}>
            <input
              type="checkbox"
              className={styles.checkbox}
              checked={selected.has(node.entry.path)}
              onChange={() => toggleArtistSelect(node)}
            />
            <button
              className={styles.expandBtn}
              onClick={() => toggleExpand(idx)}
              aria-label={node.expanded ? 'Collapse' : 'Expand'}
            >
              {node.loading ? (
                <span className={styles.spinner} />
              ) : (
                <span className={`${styles.arrow} ${node.expanded ? styles.arrowOpen : ''}`}>▶</span>
              )}
            </button>
            <span
              className={styles.artistName}
              onClick={() => toggleExpand(idx)}
              title={node.entry.path}
            >
              {node.entry.name}
            </span>
          </div>

          {node.expanded && node.albums.length > 0 && (
            <div className={styles.albumList}>
              {node.albums.map(album => (
                <div key={album.path} className={styles.albumRow}>
                  <input
                    type="checkbox"
                    className={styles.checkbox}
                    checked={selected.has(album.path)}
                    onChange={() => toggleAlbumSelect(album.path)}
                  />
                  <span className={styles.folderIcon}>📁</span>
                  <span
                    className={styles.albumName}
                    onClick={() => toggleAlbumSelect(album.path)}
                    title={album.path}
                  >
                    {album.name}
                  </span>
                </div>
              ))}
            </div>
          )}

          {node.expanded && node.albums.length === 0 && !node.loading && (
            <div className={styles.emptyAlbums}>No album folders found</div>
          )}
        </div>
      ))}
    </div>
  )
}
