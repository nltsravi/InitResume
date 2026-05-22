import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Auto-Apply Crew Dashboard',
  description: 'Autonomous job search, customization, and submission agent dashboard.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
