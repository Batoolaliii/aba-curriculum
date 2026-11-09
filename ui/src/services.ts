import { fetchAuthSession } from 'aws-amplify/auth'
import type { PortalConfig } from './config'

export interface Employee { employeeId: string; name: string; department: string; startDate: string; role: string }
export interface Leave { startDate: string; endDate: string; note: string }
export class AuthenticationError extends Error {}

async function token(kind: 'idToken' | 'accessToken') {
  const session = await fetchAuthSession().catch(() => { throw new AuthenticationError('Your session has expired. Please sign in again.') })
  const jwt = session.tokens?.[kind]?.toString()
  if (!jwt) throw new AuthenticationError('Your session has expired. Please sign in again.')
  return jwt
}

async function checked(response: Response) {
  if (response.status === 401 || response.status === 403) throw new AuthenticationError('Access expired or denied. Please sign in again; contact HR if access remains denied.')
  if (!response.ok) throw new Error(`Request failed (${response.status}). Please retry or contact support.`)
  return response
}

export function makeApi(config: PortalConfig) {
  async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
    const response = await checked(await fetch(`${config.apiUrl.replace(/\/$/, '')}/${path}`, {
      method, headers: { Authorization: await token('idToken'), 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    }))
    return response.json()
  }
  return {
    employees: (from = '', to = '') => request<{ employees: Employee[] }>(`employees${from && to ? `?hiredFrom=${from}&hiredTo=${to}` : ''}`),
    createEmployee: (body: Omit<Employee, 'employeeId'>) => request<Employee>('employees', 'POST', body),
    leave: (id: string, month = '') => request<{ leave: Leave[] }>(`employees/${encodeURIComponent(id)}/leave${month ? `?month=${month}` : ''}`),
    saveLeave: (id: string, body: Leave, update: boolean) => request<Leave>(`employees/${encodeURIComponent(id)}/leave${update ? `/${body.startDate}` : ''}`, update ? 'PUT' : 'POST', body),
    hrRequest: (body: { user_id: string; prompt: string } | { user_id: string; start_date: string; end_date: string }) => request<{ executionArn: string }>(`hr-requests${'start_date' in body ? '/time-off' : ''}`, 'POST', body),
  }
}

// Only emit model text deltas, never tool arguments, reasoning, or raw event data.
function textDelta(data: string): string {
  if (data === '[DONE]') return ''
  const value = JSON.parse(data)
  if (value.error || value.exception) throw new Error('The assistant could not complete this response. Please try a new conversation.')
  return value.event?.contentBlockDelta?.delta?.text ?? ''
}

export async function readAgentStream(response: Response, onText: (text: string) => void) {
  if (!response.body) throw new Error('The assistant returned no response stream.')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let pending = ''
  let received = false
  const emit = (block: string) => {
    const data = block.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n')
    if (data) { const text = textDelta(data); if (text) { received = true; onText(text) } }
  }
  try {
    while (true) {
      const { value, done } = await reader.read()
      pending = (pending + decoder.decode(value, { stream: !done })).replace(/\r\n/g, '\n')
      let boundary: number
      while ((boundary = pending.indexOf('\n\n')) >= 0) { emit(pending.slice(0, boundary)); pending = pending.slice(boundary + 2) }
      if (done) { if (pending.trim()) emit(pending); break }
    }
    if (!received) throw new Error('The assistant returned no text. Its tools may have run; check records before retrying.')
  } finally { await reader.cancel(); reader.releaseLock() }
}

export async function chat(config: PortalConfig, prompt: string, sessionId: string, actorId: string, signal: AbortSignal, onText: (text: string) => void) {
  const path = `${config.agentBaseUrl}/runtimes/${encodeURIComponent(config.agentRuntimeArn)}/invocations?qualifier=DEFAULT`
  const response = await checked(await fetch(path, {
    method: 'POST', signal,
    headers: { Authorization: `Bearer ${await token('accessToken')}`, 'Content-Type': 'application/json', Accept: 'text/event-stream', 'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId },
    body: JSON.stringify({ prompt, actorId }),
  }))
  if (!response.headers.get('content-type')?.includes('text/event-stream')) throw new Error('Unexpected assistant response format. Check the runtime configuration.')
  await readAgentStream(response, onText)
}

export function validRange(start: string, end: string) { return Boolean(start && end && start <= end) }
