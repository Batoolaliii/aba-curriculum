import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Portal from './Portal'
import App from './App'
import { AuthenticationError, chat, makeApi } from './services'
import { loadConfig } from './config'
const config = { apiUrl: 'https://api.example/prod/', userPoolId: 'pool', userPoolClientId: 'client', agentRuntimeArn: 'arn', region: 'us-east-1', agentBaseUrl: '/agentcore' }
const employee = { employeeId: 'e1', name: 'Dana Ali', department: 'Design', role: 'employee', startDate: '2024-01-01' }
const api = { employees: vi.fn(), createEmployee: vi.fn(), leave: vi.fn(), saveLeave: vi.fn(), hrRequest: vi.fn() }
vi.mock('./services', async importOriginal => ({ ...await importOriginal<typeof import('./services')>(), makeApi: vi.fn(), chat: vi.fn() }))
vi.mock('./config', async importOriginal => ({ ...await importOriginal<typeof import('./config')>(), loadConfig: vi.fn() }))
vi.mock('aws-amplify', () => ({ Amplify: { configure: vi.fn() } }))
vi.mock('aws-amplify/auth', () => ({ signOut: vi.fn().mockResolvedValue(undefined) }))
vi.mock('@aws-amplify/ui-react', () => ({ Authenticator: ({ children }: { children: (value: { user: { userId: string } }) => React.ReactNode }) => children({ user: { userId: 'staff' } }) }))
const change = (id: string, value: string) => fireEvent.change(screen.getByTestId(id), { target: { value } })
const show = () => render(<Portal config={config} actorId="staff" onSignOut={vi.fn()} />)
async function select() { fireEvent.click(await screen.findByTestId('select-e1')); await screen.findByText('No leave records for this view.') }

beforeEach(() => {
  vi.resetAllMocks()
  vi.mocked(makeApi).mockReturnValue(api)
  api.employees.mockResolvedValue({ employees: [employee] })
  api.leave.mockResolvedValue({ leave: [] })
  api.createEmployee.mockResolvedValue(employee)
  api.saveLeave.mockResolvedValue({})
  api.hrRequest.mockResolvedValue({ executionArn: 'execution-123' })
})

describe('staff portal', () => {
  it('shows a failed leave request instead of empty records and recovers on retry', async () => {
    api.leave.mockRejectedValueOnce(new Error('Request failed (404).'))
    show()
    fireEvent.click(await screen.findByTestId('select-e1'))
    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to load leave records. Request failed (404).')
    expect(screen.queryByText('No leave records for this view.')).not.toBeInTheDocument()
    fireEvent.click(screen.getByTestId('refresh-leave'))
    expect(await screen.findByText('No leave records for this view.')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
  it('hides stale records when a month request fails', async () => {
    api.leave.mockResolvedValueOnce({ leave: [{ startDate: '2026-10-29', endDate: '2026-10-29', note: 'Time off' }] })
    show()
    fireEvent.click(await screen.findByTestId('select-e1'))
    await screen.findByText('2026-10-29 → 2026-10-29')
    api.leave.mockRejectedValueOnce(new Error('Network unavailable'))
    change('leave-month', '2026-11')
    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to load leave records.')
    expect(screen.queryByText('No leave records for this view.')).not.toBeInTheDocument()
    expect(screen.queryByText('2026-10-29 → 2026-10-29')).not.toBeInTheDocument()
  })
  it('returns to sign-in if the initial API request rejects the session', async () => {
    const onSignOut = vi.fn()
    api.employees.mockRejectedValueOnce(new AuthenticationError('Session expired'))
    render(<Portal config={config} actorId="staff" onSignOut={onSignOut} />)
    await waitFor(() => expect(onSignOut).toHaveBeenCalledOnce())
  })
  it('loads configured authentication and shows missing configuration errors', async () => {
    vi.mocked(loadConfig).mockRejectedValue(new Error('Portal setup is incomplete'))
    const view = render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('incomplete')
    view.unmount()
    vi.mocked(loadConfig).mockResolvedValue(config)
    render(<App />)
    expect(await screen.findByTestId('select-e1')).toHaveTextContent('Dana Ali')
  })
  it('loads directory, filters hire dates, and creates an employee', async () => {
    show(); await screen.findByTestId('select-e1')
    change('hired-from', '2024-01-01'); change('hired-to', '2026-12-31')
    fireEvent.click(screen.getByTestId('filter-employees'))
    await waitFor(() => expect(api.employees).toHaveBeenCalledWith('2024-01-01', '2026-12-31'))
    fireEvent.click(screen.getByTestId('new-employee'))
    change('employee-name', 'Dana Ali'); change('employee-department', 'Design'); change('employee-start', '2024-01-01')
    fireEvent.click(screen.getByTestId('create-employee'))
    await waitFor(() => expect(api.createEmployee).toHaveBeenCalledWith(expect.objectContaining({ name: 'Dana Ali', department: 'Design' })))
  })
  it('creates and updates leave, and filters by month', async () => {
    show(); await select()
    change('leave-start', '2026-11-10'); change('leave-end', '2026-11-12'); change('leave-note', 'Holiday')
    api.leave.mockResolvedValue({ leave: [{ startDate: '2026-11-10', endDate: '2026-11-12', note: 'Holiday' }] })
    fireEvent.click(screen.getByTestId('save-leave'))
    await waitFor(() => expect(api.saveLeave).toHaveBeenCalledWith('e1', { startDate: '2026-11-10', endDate: '2026-11-12', note: 'Holiday' }, false))
    fireEvent.click(await screen.findByTestId('edit-2026-11-10'))
    change('leave-end', '2026-11-13'); fireEvent.click(screen.getByTestId('save-leave'))
    await waitFor(() => expect(api.saveLeave).toHaveBeenLastCalledWith('e1', expect.objectContaining({ endDate: '2026-11-13' }), true))
    change('leave-month', '2026-11')
    await waitFor(() => expect(api.leave).toHaveBeenLastCalledWith('e1', '2026-11'))
  })
  it('rejects reversed date ranges without calling the API', async () => {
    show(); await select()
    change('leave-start', '2026-11-12'); change('leave-end', '2026-11-10'); fireEvent.click(screen.getByTestId('save-leave'))
    expect(await screen.findByRole('alert')).toHaveTextContent('end date')
    expect(api.saveLeave).not.toHaveBeenCalled()
    change('hired-from', '2026-11-12'); fireEvent.click(screen.getByTestId('filter-employees'))
    expect(await screen.findByRole('alert')).toHaveTextContent('both hire dates')
  })
  it('submits time-off and general requests and displays asynchronous acceptance', async () => {
    show(); await select(); fireEvent.click(screen.getByTestId('request-tab'))
    change('request-start', '2026-11-10'); change('request-end', '2026-11-12'); fireEvent.click(screen.getByTestId('submit-request'))
    await waitFor(() => expect(api.hrRequest).toHaveBeenCalledWith({ user_id: 'e1', start_date: '2026-11-10', end_date: '2026-11-12' }))
    expect(await screen.findByRole('status')).toHaveTextContent('execution-123')
    change('request-type', 'general'); change('request-prompt', 'Benefits help'); fireEvent.click(screen.getByTestId('submit-request'))
    await waitFor(() => expect(api.hrRequest).toHaveBeenLastCalledWith({ user_id: 'e1', prompt: 'Benefits help' }))
  })
  it('renders streamed chat, rotates session and cancels in-flight response', async () => {
    show(); await screen.findByTestId('select-e1')
    vi.mocked(chat).mockImplementation(async (_config, _prompt, _session, _actor, _signal, onText) => { onText('Hello Dana') })
    change('chat-prompt', 'Hello'); fireEvent.click(screen.getByTestId('send-chat'))
    expect(await screen.findByText('Hello Dana')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByTestId('new-conversation')).toBeEnabled())
    const firstSession = vi.mocked(chat).mock.calls[0][2]
    fireEvent.click(screen.getByTestId('new-conversation'))
    vi.mocked(chat).mockImplementation((_config, _prompt, _session, _actor, signal) => new Promise((_resolve, reject) => signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))))
    change('chat-prompt', 'Again'); fireEvent.click(screen.getByTestId('send-chat'))
    expect(vi.mocked(chat).mock.calls[1][2]).not.toBe(firstSession)
    fireEvent.click(screen.getByTestId('stop-chat'))
    expect(await screen.findByRole('status')).toHaveTextContent('actions may still complete')
  })
  it('shows failed directory requests and supports retry', async () => {
    api.employees.mockRejectedValueOnce(new Error('Network unavailable'))
    show()
    expect(await screen.findByRole('alert')).toHaveTextContent('Network unavailable')
    fireEvent.click(screen.getByTestId('refresh-directory'))
    expect(await screen.findByTestId('select-e1')).toBeInTheDocument()
  })
})
