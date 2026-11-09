import { describe, it, expect, vi } from 'vitest'
import { fetchAuthSession } from 'aws-amplify/auth'
import { chat, makeApi, readAgentStream, validRange } from './services'
import { validateConfig } from './config'
vi.mock('aws-amplify/auth', () => ({ fetchAuthSession: vi.fn() }))
const config = { apiUrl: 'https://api.example/prod/', userPoolId: 'us-east-1_pool', userPoolClientId: 'client', agentRuntimeArn: 'arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/test', region: 'us-east-1', agentBaseUrl: '/agentcore' }
const auth = () => vi.mocked(fetchAuthSession).mockResolvedValue({ tokens: { idToken: { toString: () => 'id' }, accessToken: { toString: () => 'access' } } } as Awaited<ReturnType<typeof fetchAuthSession>>)

describe('portal integrations', () => {
  it('validates public configuration and date ranges', () => {
    expect(validateConfig(config)).toEqual(config)
    expect(() => validateConfig({})).toThrow('incomplete')
    expect(() => validateConfig({ ...config, apiUrl: 'http://unsafe' })).toThrow('HTTPS')
    expect(validRange('2026-11-10', '2026-11-12')).toBe(true)
    expect(validRange('2026-11-12', '2026-11-10')).toBe(false)
  })
  it('uses ID token and preserves API stage path', async () => {
    auth()
    const fetcher = vi.fn().mockResolvedValue(new Response('{"employees":[]}'))
    vi.stubGlobal('fetch', fetcher)
    await makeApi(config).employees('2026-01-01', '2026-12-31')
    expect(fetcher).toHaveBeenCalledWith('https://api.example/prod/employees?hiredFrom=2026-01-01&hiredTo=2026-12-31', expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'id' }) }))
  })
  it('fails closed on missing credentials and denied API calls', async () => {
    vi.mocked(fetchAuthSession).mockResolvedValue({})
    await expect(makeApi(config).employees()).rejects.toThrow('expired')
    auth()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 403 })))
    await expect(makeApi(config).employees()).rejects.toThrow('denied')
  })
  it('decodes split SSE deltas while ignoring tool events', async () => {
    const encoder = new TextEncoder()
    const stream = new ReadableStream({ start(controller) {
    for (const chunk of ['data: {"event":{"contentBlockDelta":{"delta":{"text":"Hel', 'lo"}}}}\r', '\n\r', '\ndata: {"event":{"contentBlockStart":{"start":{"toolUse":{}}}}}\n\n']) controller.enqueue(encoder.encode(chunk))
      controller.close()
    } })
    const callback = vi.fn()
    await readAgentStream(new Response(stream), callback)
    expect(callback).toHaveBeenCalledExactlyOnceWith('Hello')
  })
  it('uses access token and the supplied conversation session for chat', async () => {
    auth()
    const fetcher = vi.fn().mockResolvedValue(new Response('data: {"event":{"contentBlockDelta":{"delta":{"text":"Hi"}}}}\n\n', { headers: { 'content-type': 'text/event-stream' } }))
    vi.stubGlobal('fetch', fetcher)
    const id = crypto.randomUUID()
    await chat(config, 'Hello', id, 'staff-1', new AbortController().signal, vi.fn())
    expect(fetcher).toHaveBeenCalledWith(expect.stringContaining('/agentcore/runtimes/arn%3Aaws'), expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer access', 'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': id }) }))
    expect(id.length).toBeGreaterThanOrEqual(33)
  })
  it('surfaces empty and malformed assistant responses', async () => {
    await expect(readAgentStream(new Response('data: {}\n\n'), vi.fn())).rejects.toThrow('no text')
    await expect(readAgentStream(new Response('data: not-json\n\n'), vi.fn())).rejects.toThrow()
  })
})
