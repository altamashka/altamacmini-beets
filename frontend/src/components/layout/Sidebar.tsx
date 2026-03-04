import { NavLink } from 'react-router-dom'
import styles from './Sidebar.module.css'

const nav = [
  { to: '/import', label: 'Import', icon: '↓' },
  { to: '/cleaner', label: 'Library Cleaner', icon: '✦' },
]

export function Sidebar() {
  return (
    <nav className={styles.sidebar}>
      <div className={styles.logo}>beets-manager</div>
      {nav.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
        >
          <span className={styles.icon}>{icon}</span>
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
