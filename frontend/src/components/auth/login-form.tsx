'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { AuthService } from '@/lib/auth/auth-service'
import { RememberMeService } from '@/lib/auth/remember-me-service'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Mail, Lock } from 'lucide-react'

export function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isAutoLoginAttempt, setIsAutoLoginAttempt] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  // Auto-login on component mount if Remember Me is enabled
  useEffect(() => {
    const attemptAutoLogin = async () => {
      console.log('🔄 Checking for auto-login credentials...')
      
      if (RememberMeService.isRememberMeEnabled()) {
        const savedCredentials = await RememberMeService.attemptAutoLogin()
        
        if (savedCredentials) {
          setIsAutoLoginAttempt(true)
          setIsLoading(true)
          setEmail(savedCredentials.email)
          setRememberMe(true)
          
          console.log('🚀 Attempting auto-login for:', savedCredentials.email)
          
          try {
            await AuthService.signIn(savedCredentials.email, savedCredentials.password)
            console.log('✅ Auto-login successful')
            router.push('/chat')
          } catch (error) {
            console.warn('❌ Auto-login failed:', error)
            // Clear invalid credentials
            RememberMeService.clearSavedCredentials()
            setError('Auto-login failed. Please sign in manually.')
          } finally {
            setIsLoading(false)
            setIsAutoLoginAttempt(false)
          }
        }
      } else {
        // Pre-fill email if available (even without auto-login)
        const savedEmail = RememberMeService.getSavedEmail()
        if (savedEmail) {
          setEmail(savedEmail)
        }
      }
    }

    attemptAutoLogin()
  }, [router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      // Attempt login first - only save credentials after successful authentication
      await AuthService.signIn(email, password)
      console.log('✅ Manual login successful')
      
      // Only save credentials AFTER successful login
      if (rememberMe) {
        RememberMeService.saveCredentials(email, password, rememberMe)
        console.log('💾 Credentials saved for Remember Me (7 days)')
      } else {
        // Clear any existing credentials if user unchecked Remember Me
        RememberMeService.clearSavedCredentials()
        console.log('🧹 Remember Me disabled, credentials cleared')
      }
      
      router.push('/chat')
    } catch (error) {
      // Determine if error is due to invalid credentials vs network/server issues
      const errorMessage = error instanceof Error ? error.message : 'Failed to sign in. Please try again.'
      const isCredentialError = errorMessage.toLowerCase().includes('credential') || 
                                errorMessage.toLowerCase().includes('password') ||
                                errorMessage.toLowerCase().includes('email') ||
                                errorMessage.toLowerCase().includes('unauthorized')
      
      // Only clear saved credentials if the error is specifically about invalid credentials
      // Keep credentials for network errors, server issues, etc.
      if (rememberMe && isCredentialError) {
        RememberMeService.clearSavedCredentials()
        console.log('🚫 Invalid credentials detected, cleared saved Remember Me data')
      }
      
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-2xl font-bold text-white">V</span>
            </div>
          </div>
          <CardTitle className="text-2xl text-center">Welcome to VOXY</CardTitle>
          <CardDescription className="text-center">
            Sign in to your account to continue
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-9"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-9"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>
            
            {/* Remember Me Checkbox */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="remember-me"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(checked as boolean)}
                disabled={isLoading}
              />
              <Label 
                htmlFor="remember-me" 
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
              >
                Remember me for 7 days
              </Label>
            </div>
            
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {isAutoLoginAttempt ? 'Auto-signing in...' : 'Signing in...'}
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>
          
          <div className="mt-6 space-y-4">
            <div className="text-center text-sm">
              <Link 
                href="/auth/reset-password" 
                className="text-primary hover:underline"
              >
                Forgot your password?
              </Link>
            </div>
            
            <div className="text-center text-sm">
              Don&apos;t have an account?{' '}
              <Link 
                href="/auth/signup" 
                className="text-primary hover:underline font-medium"
              >
                Sign up
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}