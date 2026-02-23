import * as React from 'react'

const MOBILE_BREAKPOINT = 768

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState(false)

  React.useEffect(() => {
    const checkDevice = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }

    // Initial check
    checkDevice()

    // Listen for changes
    window.addEventListener('resize', checkDevice)

    // Cleanup
    return () => {
      window.removeEventListener('resize', checkDevice)
    }
  }, [])

  return isMobile
}
