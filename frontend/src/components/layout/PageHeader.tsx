import type { ReactNode } from 'react'
import Icon from '../ui/Icon'

type PageHeaderProps = {
  title: string
  subtitle?: string
  eyebrow?: ReactNode
  actions?: ReactNode
}

export default function PageHeader({ title, subtitle, eyebrow, actions }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div className="page-header__content">
        {eyebrow && <div className="page-header__eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <div className="page-header__actions">
        {actions}
        <button className="icon-button notification-button" type="button" aria-label="Notifications">
          <Icon name="bell" />
          <span className="notification-button__dot" />
        </button>
        <button className="season-selector" type="button" aria-label="Select season">
          <span>2026/27 Season</span>
          <Icon name="chevron" />
        </button>
      </div>
    </header>
  )
}
