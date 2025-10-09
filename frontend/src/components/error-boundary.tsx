'use client'

import { useEffect } from 'react'
import { errorHandler } from '@/lib/utils/error-handler'

/**
 * Error Boundary Component for Global Error Handling
 */
export default function ErrorBoundary({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Initialize global error handlers
    errorHandler.setupGlobalHandlers()
    
    return () => {
      // Cleanup if needed (remove event listeners)
      console.log('🛡️ Error boundary cleanup')
    }
  }, [])

  return <>{children}</>
}