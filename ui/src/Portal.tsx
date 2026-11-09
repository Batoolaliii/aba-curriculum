import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { PortalConfig } from './config'
import { AuthenticationError, chat, makeApi, validRange } from './services'
import type { Employee, Leave } from './services'

const fields = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); return Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string> }
const message = (error: unknown) => error instanceof Error ? error.message : 'Something went wrong. Please retry.'

export default function Portal({ config, actorId, onSignOut }: { config: PortalConfig; actorId: string; onSignOut: () => void }) {
  const api = useMemo(() => makeApi(config), [config])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [selected, setSelected] = useState<Employee | null>(null)
  const [leave, setLeave] = useState<Leave[]>([])
  const [editing, setEditing] = useState<Leave | null>(null)
  const [month, setMonth] = useState('')
  const [loading, setLoading] = useState(true)
  const [leaveLoading, setLeaveLoading] = useState(false)
  const [leaveError, setLeaveError] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [tab, setTab] = useState('leave')
  const [showCreate, setShowCreate] = useState(false)
  const [search, setSearch] = useState('')
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([])
  const [prompt, setPrompt] = useState('')
  const [streaming, setStreaming] = useState(false)
  const session = useRef(crypto.randomUUID())
  const controller = useRef<AbortController | null>(null)
  const selection = useRef(0)
  const fail = useCallback((reason: unknown) => {
    setError(message(reason))
    if (reason instanceof AuthenticationError) { controller.current?.abort(); onSignOut() }
  }, [onSignOut])
  useEffect(() => {
    let alive = true
    api.employees().then(data => { if (alive) setEmployees(data.employees) }).catch(reason => { if (alive) fail(reason) }).finally(() => { if (alive) setLoading(false) })
    return () => { alive = false; controller.current?.abort() }
  }, [api, fail])
  async function refreshLeave(employee: Employee, filter: string) {
    const requestId = ++selection.current
    setLeaveError('')
    setLeaveLoading(true)
    try { const data = await api.leave(employee.employeeId, filter); if (selection.current === requestId) setLeave(data.leave) }
    catch (reason) {
      if (selection.current === requestId) {
        setLeaveError(`Unable to load leave records. ${message(reason)}`)
        if (reason instanceof AuthenticationError) fail(reason)
      }
    }
    finally { if (selection.current === requestId) setLeaveLoading(false) }
  }
  function choose(employee: Employee) { setSelected(employee); setEditing(null); setLeave([]); setError(''); setNotice(''); void refreshLeave(employee, month) }
  async function perform(name: string, action: () => Promise<void>) {
    if (busy) return
    setBusy(name); setError(''); setNotice('')
    try { await action() } catch (reason) { fail(reason) } finally { setBusy('') }
  }
  async function filterEmployees(event: FormEvent<HTMLFormElement>) {
    const data = fields(event)
    if ((data.from || data.to) && !validRange(data.from, data.to)) { setError('Choose both hire dates in chronological order.'); return }
    await perform('filter', async () => { const result = await api.employees(data.from, data.to); setEmployees(result.employees); setSelected(null); selection.current++; setLeave([]) })
  }
  async function createEmployee(event: FormEvent<HTMLFormElement>) {
    const data = fields(event)
    if (!data.name.trim() || !data.department.trim()) { setError('Name and department cannot be blank.'); return }
    await perform('employee', async () => {
      const employee = await api.createEmployee({ name: data.name.trim(), department: data.department.trim(), startDate: data.startDate, role: data.role.trim() || 'employee' })
      setEmployees((await api.employees()).employees); setShowCreate(false); choose(employee); setNotice('Employee created.')
    })
  }
  async function saveLeave(event: FormEvent<HTMLFormElement>) {
    const data = fields(event)
    if (!selected || !validRange(data.startDate, data.endDate)) { setError('Leave end date must be on or after the start date.'); return }
    const employee = selected
    await perform('leave', async () => { await api.saveLeave(employee.employeeId, { startDate: data.startDate, endDate: data.endDate, note: data.note }, Boolean(editing)); setEditing(null); await refreshLeave(employee, month); setNotice('Leave record saved.') })
  }
  async function submitRequest(event: FormEvent<HTMLFormElement>) {
    const data = fields(event)
    if (!selected) return
    if (data.type === 'time-off' && !validRange(data.start_date, data.end_date)) { setError('Request end date must be on or after the start date.'); return }
    if (data.type === 'general' && !data.prompt.trim()) { setError('Enter a request message.'); return }
    await perform('request', async () => {
      const result = await api.hrRequest(data.type === 'time-off' ? { user_id: selected.employeeId, start_date: data.start_date, end_date: data.end_date } : { user_id: selected.employeeId, prompt: data.prompt.trim() })
      setNotice(`Request accepted for processing. Execution: ${result.executionArn}. This is not approval or confirmation of delivery.`)
    })
  }
  async function sendChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!prompt.trim() || streaming) return
    const text = prompt.trim(); setPrompt(''); setStreaming(true); setError('')
    setMessages(previous => [...previous, { role: 'You', text }, { role: 'hrAgent', text: '' }])
    const aborter = new AbortController(); controller.current = aborter
    try { await chat(config, text, session.current, actorId, aborter.signal, delta => setMessages(previous => previous.map((entry, index) => index === previous.length - 1 ? { ...entry, text: entry.text + delta } : entry))) }
    catch (reason) { if (aborter.signal.aborted) setNotice('Response stopped. Agent actions may still complete; check records before retrying.'); else fail(reason) }
    finally { setStreaming(false); controller.current = null }
  }
  const filtered = employees.filter(employee => `${employee.name} ${employee.department} ${employee.employeeId}`.toLowerCase().includes(search.toLowerCase()))
  return <div className="portal">
    <aside className="rail"><a className="brand" href="#workspace" aria-label="HR home">h<span>r</span><i>●</i></a><div className="rail-label">WORKSPACE</div><a className="nav-item active" href="#workspace">▦ <span>People & leave</span></a><a className="nav-item" href="#assistant">✧ <span>HR assistant</span></a><div className="rail-bottom"><span className="avatar">HR</span><div><strong>HR workspace</strong><small>Trusted staff access</small></div></div></aside>
    <div className="main-shell"><header className="topbar"><span>WORKSPACE <b>/</b> People & leave</span><button data-testid="sign-out" className="quiet" onClick={() => { controller.current?.abort(); onSignOut() }}>Sign out ↗</button></header>
    <main id="workspace"><div className="page-heading"><div><p className="eyebrow">YOUR PEOPLE, TAKEN CARE OF</p><h1>People & leave</h1><p>Manage employee records and keep HR requests moving.</p></div><button data-testid="new-employee" onClick={() => setShowCreate(!showCreate)}>+ Add employee</button></div>
    {error && <div className="alert error" role="alert">{error}<button className="quiet" data-testid="dismiss-error" onClick={() => setError('')}>Dismiss</button></div>}
    {notice && <div className="alert success" role="status">{notice}</div>}
    <div className="metrics"><div><span>Employee records</span><strong>{loading ? '—' : employees.length}</strong><small>In the current directory view</small></div><div><span>Selected employee</span><strong>{selected?.name || 'Not selected'}</strong><small>{selected ? selected.department : 'Choose someone to manage leave'}</small></div><div className="metric-note"><span className="status-dot"/><div><strong>One connected workspace</strong><small>Directory, leave and your HR assistant</small></div></div></div>
    {showCreate && <section className="card create-card"><h2>Add an employee</h2><form onSubmit={createEmployee} className="form-grid"><label>Name<input data-testid="employee-name" name="name" required /></label><label>Department<input data-testid="employee-department" name="department" required /></label><label>Hire date<input data-testid="employee-start" name="startDate" type="date" required /></label><label>Role<input data-testid="employee-role" name="role" defaultValue="employee" required /></label><button data-testid="create-employee" disabled={Boolean(busy)}>Create employee</button><button data-testid="cancel-employee" type="button" className="secondary" onClick={() => setShowCreate(false)}>Cancel</button></form></section>}
    <div className="workspace-grid"><section className="card directory"><div className="section-heading"><div><p className="eyebrow">THE TEAM</p><h2>Employee directory</h2></div><span className="count">{employees.length}</span></div><label className="search-label">Search employees<input data-testid="employee-search" placeholder="Search by name, team or ID" value={search} onChange={event => setSearch(event.target.value)} /></label><form onSubmit={filterEmployees} className="date-filter"><label>Hired from<input data-testid="hired-from" name="from" type="date" /></label><label>Hired to<input data-testid="hired-to" name="to" type="date" /></label><button data-testid="filter-employees" className="secondary" disabled={Boolean(busy)}>Apply</button></form>
    {loading ? <p role="status">Loading employees…</p> : filtered.length ? <ul className="employee-list">{filtered.map(employee => <li key={employee.employeeId}><button data-testid={`select-${employee.employeeId}`} className={`employee-row ${selected?.employeeId === employee.employeeId ? 'selected' : ''}`} disabled={Boolean(busy)} onClick={() => choose(employee)}><span className="avatar">{employee.name.slice(0, 2).toUpperCase()}</span><span><strong>{employee.name}</strong><small>{employee.department} · {employee.role}</small><small className="employee-id">{employee.employeeId}</small></span><span className="row-arrow">↗</span></button></li>)}</ul> : <div className="empty"><span>◇</span><h3>No employees found</h3><p>Add an employee or adjust your filters.</p></div>}
    <button data-testid="refresh-directory" className="quiet refresh" disabled={Boolean(busy)} onClick={() => void perform('refresh', async () => setEmployees((await api.employees()).employees))}>↻ Refresh directory</button></section>
    <section className="card details"><div className="section-heading"><div><p className="eyebrow">EMPLOYEE WORKSPACE</p><h2>{selected?.name || 'Make room for time off'}</h2></div>{selected && <span className="tag">{selected.department}</span>}</div>{!selected ? <div className="empty detail-empty"><span>☷</span><h3>A little space for your people</h3><p>Select an employee to view leave records, save time off or send a request to HR.</p></div> : <><div className="employee-meta">Joined {selected.startDate} <span>·</span> ID {selected.employeeId}</div><div className="tabs"><button data-testid="leave-tab" className={tab === 'leave' ? 'active' : ''} onClick={() => setTab('leave')}>Leave records</button><button data-testid="request-tab" className={tab === 'requests' ? 'active' : ''} onClick={() => setTab('requests')}>HR requests</button></div>
    {tab === 'leave' ? <><div className="leave-heading"><h3>Recorded leave</h3><label>Month<input data-testid="leave-month" disabled={Boolean(busy)} type="month" value={month} onChange={event => { setMonth(event.target.value); void refreshLeave(selected, event.target.value) }} /></label><button data-testid="refresh-leave" className="quiet" onClick={() => void refreshLeave(selected, month)}>Refresh</button></div>{leaveLoading ? <p role="status">Loading leave…</p> : leaveError ? <p role="alert">{leaveError} Use Refresh to retry.</p> : leave.length ? <ul className="leave-list">{leave.map(record => <li key={record.startDate}><div><strong>{record.startDate} → {record.endDate}</strong><p>{record.note || 'No note added'}</p></div><button data-testid={`edit-${record.startDate}`} className="quiet" onClick={() => setEditing(record)}>Edit</button></li>)}</ul> : <p className="muted">No leave records for this view.</p>}<form key={`${selected.employeeId}-${editing?.startDate || 'new'}`} onSubmit={saveLeave} className="form-grid leave-form"><h3>{editing ? 'Update leave' : 'Record leave'}</h3><label>Start date<input data-testid="leave-start" name="startDate" type="date" defaultValue={editing?.startDate} readOnly={Boolean(editing)} required /></label><label>End date<input data-testid="leave-end" name="endDate" type="date" defaultValue={editing?.endDate} required /></label><label className="full">Note<textarea data-testid="leave-note" name="note" defaultValue={editing?.note} placeholder="Add context for your team" /></label><button data-testid="save-leave" disabled={Boolean(busy)}>Save leave record</button>{editing && <button type="button" data-testid="cancel-edit" className="secondary" onClick={() => setEditing(null)}>Cancel edit</button>}<small className="full muted">Saving a record does not submit an HR approval request.</small></form></> : <form onSubmit={submitRequest} className="form-grid request-form"><h3>Send a request to HR</h3><label className="full">Request type<select data-testid="request-type" name="type" defaultValue="time-off" onChange={event => { const form = event.target.form; if (form) { const type = event.target.value; (form.elements.namedItem('prompt') as HTMLTextAreaElement).required = type === 'general' } }}><option value="time-off">Time off</option><option value="general">General HR question</option></select></label><label>From<input data-testid="request-start" name="start_date" type="date" /></label><label>To<input data-testid="request-end" name="end_date" type="date" /></label><label className="full">Message (general requests)<textarea data-testid="request-prompt" name="prompt" placeholder="How can HR help?" /></label><button data-testid="submit-request" disabled={Boolean(busy)}>Submit request ↗</button><p className="full muted">Requests run asynchronously. Acceptance confirms submission, not approval or delivery.</p></form>}</> }</section></div>
    <section id="assistant" className="card assistant"><div className="section-heading"><div className="assistant-title"><span className="assistant-icon">✧</span><div><p className="eyebrow">A HELPING HAND</p><h2>Ask hrAgent</h2></div></div><button data-testid="new-conversation" className="secondary" disabled={streaming} onClick={() => { session.current = crypto.randomUUID(); setMessages([]); setNotice('New conversation started.') }}>New conversation</button></div><p className="assistant-warning">hrAgent can change employee and leave records and send HR notifications. Check important details before asking it to act.</p><div className="conversation" role="log" aria-live="polite" aria-label="Assistant conversation">{messages.length ? messages.map((entry, index) => <div className={`bubble ${entry.role === 'You' ? 'user' : ''}`} key={index}><strong>{entry.role}</strong><p>{entry.text || (streaming ? 'Thinking…' : 'No text received.')}</p></div>) : <div className="chat-empty"><h3>What can we take off your plate?</h3><p>Ask an HR question or request help with employee and leave records.</p></div>}</div><form className="chat-composer" onSubmit={sendChat}><label htmlFor="chat-prompt" className="sr-only">Message hrAgent</label><textarea id="chat-prompt" data-testid="chat-prompt" value={prompt} onChange={event => setPrompt(event.target.value)} placeholder="Ask hrAgent a question…" required disabled={streaming} /><button data-testid="send-chat" disabled={streaming || !prompt.trim()}>Send ↗</button>{streaming && <button data-testid="stop-chat" type="button" className="secondary" onClick={() => controller.current?.abort()}>Stop response</button>}</form><small className="muted">AI responses can be inaccurate. Refresh records after asking the assistant to make changes.</small></section><footer>HR Leave Portal <span>People first. Details in place.</span></footer></main></div>
  </div>
}
