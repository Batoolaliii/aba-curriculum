import { useEffect, useState } from 'react'
import { Amplify } from 'aws-amplify'
import { Authenticator } from '@aws-amplify/ui-react'
import { signOut } from 'aws-amplify/auth'
import '@aws-amplify/ui-react/styles.css'
import { loadConfig } from './config'
import type { PortalConfig } from './config'
import Portal from './Portal'
import './App.css'

export default function App() {
  const [config, setConfig] = useState<PortalConfig | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let alive = true
    loadConfig().then(value => {
      Amplify.configure({ Auth: { Cognito: { userPoolId: value.userPoolId, userPoolClientId: value.userPoolClientId, loginWith: { email: true } } } })
      if (alive) setConfig(value)
    }).catch(reason => { if (alive) setError(reason instanceof Error ? reason.message : 'Unable to load configuration.') })
    return () => { alive = false }
  }, [])
  if (error) return <main className="setup"><p className="eyebrow">HR LEAVE PORTAL</p><h1>Let's get connected.</h1><p role="alert">{error}</p><button data-testid="retry-config" onClick={() => location.reload()}>Retry setup</button></main>
  if (!config) return <main className="setup" role="status">Loading your workspace…</main>
  return <Authenticator hideSignUp loginMechanisms={['email']}>{({ user }) => <Portal config={config} actorId={user?.userId || ''} onSignOut={() => void signOut()} />}</Authenticator>
}
