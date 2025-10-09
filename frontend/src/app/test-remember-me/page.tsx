'use client'

import { RememberMeService, useRememberMeStore } from '@/lib/auth/remember-me-service'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function TestRememberMePage() {
  const { credentials } = useRememberMeStore()

  const handleTestSave = () => {
    RememberMeService.saveCredentials('test@example.com', 'testpassword123', true)
    console.log('✅ Test credentials saved')
  }

  const handleTestGet = () => {
    const saved = RememberMeService.getSavedCredentials()
    console.log('📄 Saved credentials:', saved)
    alert(saved ? `Email: ${saved.email}` : 'No credentials found')
  }

  const handleClear = () => {
    RememberMeService.clearSavedCredentials()
    console.log('🧹 Credentials cleared')
  }

  const isRemembered = RememberMeService.isRememberMeEnabled()

  return (
    <div className="min-h-screen p-8 bg-background">
      <div className="max-w-2xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Remember Me Functionality Test</CardTitle>
            <CardDescription>
              Test the Remember Me service implementation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <Button onClick={handleTestSave} variant="default">
                Save Test Credentials
              </Button>
              
              <Button onClick={handleTestGet} variant="outline">
                Get Saved Credentials
              </Button>
              
              <Button onClick={handleClear} variant="destructive">
                Clear Credentials
              </Button>
            </div>

            <div className="p-4 bg-muted rounded-lg space-y-2">
              <h3 className="font-medium">Current State:</h3>
              <p><strong>Remember Me Enabled:</strong> {isRemembered ? '✅ Yes' : '❌ No'}</p>
              {credentials && (
                <>
                  <p><strong>Email:</strong> {credentials.email}</p>
                  <p><strong>Timestamp:</strong> {new Date(credentials.timestamp).toLocaleString()}</p>
                  <p><strong>Age:</strong> {Math.round((Date.now() - credentials.timestamp) / 1000 / 60)} minutes</p>
                </>
              )}
            </div>

            <div className="text-sm text-muted-foreground">
              <p><strong>Instructions:</strong></p>
              <ul className="list-disc list-inside space-y-1">
                <li>Click &quot;Save Test Credentials&quot; to store dummy credentials</li>
                <li>Click &quot;Get Saved Credentials&quot; to retrieve and display them</li>
                <li>Click &quot;Clear Credentials&quot; to remove stored data</li>
                <li>Check the browser console for detailed logs</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Integration Test</CardTitle>
            <CardDescription>
              Go to the login page to test the full Remember Me flow
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <a href="/auth/login">Go to Login Page</a>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}