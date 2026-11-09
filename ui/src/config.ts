export interface PortalConfig {
  apiUrl: string
  userPoolId: string
  userPoolClientId: string
  agentRuntimeArn: string
  region: string
  agentBaseUrl: string
}

export function validateConfig(value: Partial<PortalConfig>): PortalConfig {
  const missing = ['apiUrl', 'userPoolId', 'userPoolClientId', 'agentRuntimeArn', 'region'].filter(key => !value[key as keyof PortalConfig])
  if (missing.length) throw new Error(`Portal setup is incomplete: ${missing.join(', ')}. See ui/README.md.`)
  if (!/^https:\/\//.test(value.apiUrl!)) throw new Error('The API URL must use HTTPS.')
  if (!value.agentRuntimeArn!.startsWith('arn:aws:bedrock-agentcore:')) throw new Error('Invalid AgentCore runtime ARN.')
  return { ...value, agentBaseUrl: value.agentBaseUrl || '/agentcore' } as PortalConfig
}

export async function loadConfig(): Promise<PortalConfig> {
  if (import.meta.env.VITE_API_URL) return validateConfig({
    apiUrl: import.meta.env.VITE_API_URL,
    userPoolId: import.meta.env.VITE_USER_POOL_ID,
    userPoolClientId: import.meta.env.VITE_USER_POOL_CLIENT_ID,
    agentRuntimeArn: import.meta.env.VITE_AGENT_RUNTIME_ARN,
    region: import.meta.env.VITE_AWS_REGION,
    agentBaseUrl: '/agentcore',
  })
  const response = await fetch('/config.json', { cache: 'no-store' })
  if (!response.ok) throw new Error('Portal configuration is missing. Configure ui/.env.local using ui/.env.example, or deploy the UI configuration.')
  return validateConfig(await response.json())
}
