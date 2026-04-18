import type { MouseEvent as ReactMouseEvent } from 'react'

export function applyTilt(event: ReactMouseEvent<HTMLElement>) {
  const rect = event.currentTarget.getBoundingClientRect()
  const x = (event.clientX - rect.left) / rect.width
  const y = (event.clientY - rect.top) / rect.height
  const rotateY = (x - 0.5) * 14
  const rotateX = (0.5 - y) * 12

  event.currentTarget.style.setProperty('--tilt-x', `${rotateX.toFixed(2)}deg`)
  event.currentTarget.style.setProperty('--tilt-y', `${rotateY.toFixed(2)}deg`)
  event.currentTarget.style.setProperty('--glow-x', `${(x * 100).toFixed(2)}%`)
  event.currentTarget.style.setProperty('--glow-y', `${(y * 100).toFixed(2)}%`)
}

export function resetTilt(event: ReactMouseEvent<HTMLElement>) {
  event.currentTarget.style.setProperty('--tilt-x', '0deg')
  event.currentTarget.style.setProperty('--tilt-y', '0deg')
  event.currentTarget.style.setProperty('--glow-x', '50%')
  event.currentTarget.style.setProperty('--glow-y', '50%')
}
