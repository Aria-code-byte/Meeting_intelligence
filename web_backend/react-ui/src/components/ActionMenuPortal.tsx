import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'

interface MenuPosition {
  top: number
  left: number
  direction: 'down' | 'up'
}

interface ActionMenuPortalProps {
  open: boolean
  position: MenuPosition | null
  onClose: () => void
  children: React.ReactNode
}

export function ActionMenuPortal({ open, position, onClose, children }: ActionMenuPortalProps) {
  const menuRef = useRef<HTMLDivElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    if (!open) return

    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open, onClose])

  // Close menu on scroll or resize
  useEffect(() => {
    if (!open) return

    const handleClose = () => onClose()

    window.addEventListener('scroll', handleClose, true)
    window.addEventListener('resize', handleClose)

    return () => {
      window.removeEventListener('scroll', handleClose, true)
      window.removeEventListener('resize', handleClose)
    }
  }, [open, onClose])

  // Don't render if position is null or not open
  if (!open || !position) return null

  return createPortal(
    <div
      ref={menuRef}
      className="fixed z-[1000]"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
      }}
    >
      {children}
    </div>,
    document.body
  )
}
