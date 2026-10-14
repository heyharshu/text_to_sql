import { useEffect, useRef, useState } from 'react'
import { ArrowUp, Check, ChevronDown, Code2, Copy, Database, Download, Loader2, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const examples = ['How many orders do we have by status?', 'Which 10 products earned the most revenue?', 'Which regions have the most customers?', 'Show monthly sales for 2025.']

function downloadCsv(message) {
  const cell = (value) => {
    let text = value == null ? '' : String(value)
    if (typeof value === 'string' && /^[\s]*[=+\-@]/.test(text)) text = "'" + text
    return '"' + text.replaceAll('"', '""') + '"'
  }
  const csv = [message.columns, ...message.rows].map(row => row.map(cell).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'query-results.csv'
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function Answer({ message }) {
  const [copied, setCopied] = useState(false)
  async function copySql() {
    try {
      await navigator.clipboard.writeText(message.sql)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch { setCopied(false) }
  }
  return <article className="message">
    <div className="assistant-label"><Database size={14} /> Ask your data</div>
    <p className={`answer ${message.status === 'error' ? 'error-answer' : ''}`}>{message.answer}</p>
    {message.rows?.length > 0 && <div className="result-table">
      <Table aria-label="Query results">
        <TableHeader><TableRow>{message.columns.map((column, index) => <TableHead key={index}>{column.replaceAll('_', ' ')}</TableHead>)}</TableRow></TableHeader>
        <TableBody>{message.rows.map((row, index) => <TableRow key={index}>{row.map((value, column) => <TableCell key={column}>{value === null ? <span className="text-muted-foreground">—</span> : String(value)}</TableCell>)}</TableRow>)}</TableBody>
      </Table>
    </div>}
    {message.sql && <>
      <p className="result-meta">{message.rows.length} rows · {message.seconds.toFixed(2)}s · Read-only{message.at_limit ? ' · Row limit reached; more rows may match.' : ''}</p>
      {message.assumptions?.length > 0 && <p className="assumptions">Assumptions: {message.assumptions.join(' · ')}</p>}
      <Collapsible>
        <div className="sql-tools">
          <CollapsibleTrigger asChild><Button variant="ghost" size="sm"><Code2 size={14} /> View SQL <ChevronDown size={13} /></Button></CollapsibleTrigger>
          <Button variant="ghost" size="sm" onClick={() => downloadCsv(message)}><Download size={14} /> CSV</Button>
        </div>
        <CollapsibleContent><div className="sql-panel">
          <div className="sql-heading"><span>POSTGRESQL · VALIDATED QUERY</span><Button variant="ghost" size="sm" onClick={copySql}>{copied ? <Check size={13} /> : <Copy size={13} />}{copied ? 'Copied' : 'Copy'}</Button></div>
          <pre><code>{message.sql}</code></pre>
        </div></CollapsibleContent>
      </Collapsible>
    </>}
  </article>
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const revenueScope = 'completed'
  const discount = 'fraction'
  const [history, setHistory] = useState([])
  const [pending, setPending] = useState(null)
  const bottom = useRef(null)
  const input = useRef(null)
  const inFlight = useRef(false)

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, busy])

  async function send(text = draft) {
    const message = text.trim()
    if (!message || inFlight.current) return
    inFlight.current = true
    setBusy(true)
    setDraft('')
    setMessages(current => [...current, { role: 'user', text: message }])
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 240000)
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Chat-Client': 'ask-your-data' },
        body: JSON.stringify({ message, history, pending, revenue_scope: revenueScope, discount }),
        signal: controller.signal,
      })
      const answer = await response.json()
      if (!response.ok) throw new Error(answer.answer || 'That message couldn’t be processed. Please try a shorter question.')
      setMessages(current => [...current, { role: 'assistant', ...answer }])
      setPending(answer.pending ?? null)
      if (answer.context) setHistory(current => [...current, answer.context].slice(-4))
    } catch (error) {
      const answer = error.name === 'AbortError' ? 'That took too long. Try a more specific question.' : error instanceof TypeError ? 'Couldn’t reach the app. Make sure the Python server is running.' : error.message
      setMessages(current => [...current, { role: 'assistant', status: 'error', answer }])
    } finally {
      clearTimeout(timeout)
      inFlight.current = false
      setBusy(false)
      requestAnimationFrame(() => input.current?.focus())
    }
  }

  return <div className="app">
    <header className="topbar">
      <div className="brand"><div className="brand-icon"><MessageSquare size={19} /></div><div><div className="brand-name">Ask your data</div><div className="brand-note">Project By Harsh Gupta</div></div></div>
    </header>
    <main className="workspace">
      {messages.length === 0 && <section className="intro">
        <div className="eyebrow">YOUR DATA, IN PLAIN ENGLISH</div>
        <h1>What would you like<br />to find out?</h1>
        <p>Say hello, ask about your sales, or follow a hunch.<br />I’ll look up the numbers. You can check the SQL.</p>
        <div className="suggestions">{examples.map(example => <Button key={example} variant="outline" className="suggestion" onClick={() => send(example)}>{example}</Button>)}</div>
      </section>}
      <section className="conversation" aria-label="Conversation" aria-live="polite" aria-busy={busy}>
        {messages.map((message, index) => message.role === 'user' ? <article key={index} className="message user-message"><div className="user-bubble">{message.text}</div></article> : <Answer key={index} message={message} />)}
        {busy && <div className="thinking" role="status"><Loader2 className="spinner" size={16} /> Thinking it through…</div>}
        <div ref={bottom} />
      </section>
    </main>
    <footer className="composer-wrap">
      <form className="composer" onSubmit={event => { event.preventDefault(); send() }}>
        <Textarea ref={input} aria-label="Your message" placeholder={pending ? 'Add the detail I asked for…' : 'Ask a question, or just say hi…'} value={draft} maxLength={2000} disabled={busy} onChange={event => setDraft(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); send() } }} />
        <div className="composer-actions"><span className="composer-note">{pending ? 'Replying to a clarification · Enter to send' : 'Enter to send'}</span><Button type="submit" size="icon" aria-label="Send message" disabled={busy || !draft.trim()}>{busy ? <Loader2 size={17} className="spinner" /> : <ArrowUp size={19} />}</Button></div>
      </form>
      <div className="project-footer">
        <span>Built by Harsh Gupta</span>
        <a href="https://www.linkedin.com/in/harsh-gupta-heytechie/" target="_blank" rel="noopener noreferrer">LinkedIn</a>
        <a href="https://github.com/heyharshu" target="_blank" rel="noopener noreferrer">GitHub</a>
      </div>
    </footer>
  </div>
}
