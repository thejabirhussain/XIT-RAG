import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Source {
  url: string
  title: string
  section: string | null
  snippet: string
  char_start: number
  char_end: number
  score: number
}

interface ChatResponse {
  answer_text: string
  sources: Source[]
  confidence: 'low' | 'medium' | 'high'
  query_embedding_similarity: number[]
  follow_up_questions?: string[]
  generated_sql?: string | null
  active_collection?: string | null
}

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  follow_up_questions?: string[]
  generated_sql?: string | null
  active_collection?: string | null
}

const SUGGESTION_CHIPS = [
  {
    text: 'Show me all published policies',
    color: 'from-[#43A6F6] to-[#2E8FE3]',
  },
  {
    text: 'What are the rules for data privacy?',
    color: 'from-[#B1668E] to-[#9B4F77]',
  },
  {
    text: 'How many mitigated risks do we have?',
    color: 'from-[#F0A24E] to-[#DC8E3B]',
  },
  {
    text: 'List all open risks in the database',
    color: 'from-[#6FA874] to-[#5B9362]',
  },
  {
    text: 'List all users and their roles',
    color: 'from-[#7C73B8] to-[#675EA4]',
  },
  {
    text: 'Show current SOC 2 controls',
    color: 'from-[#66A698] to-[#4F907F]',
  },
]

export function App() {
  const [query, setQuery] = useState('')
  const [hasSubmitted, setHasSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  
  // Sidebar state
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  // Scroll ref
  const chatEndRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading])

  // Helpers to cleanly format source labels and canonical URLs
  function canonicalizeUrl(u: string): string {
    try {
      const url = new URL(u)
      return `${url.origin}${url.pathname}`
    } catch {
      return u
    }
  }

  function slugToTitleCase(slug: string): string {
    return slug
      .replace(/[-_]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase())
  }

  function cleanSourceLabel(source: Source): string {
    let t = (source.title || '').replace(/\s+/g, ' ').trim()
    t = t.replace(/\s+—\s*excerpt:.*$/i, '').replace(/\s+-\s*excerpt:.*$/i, '')
    if (t) return t
    try {
      const url = new URL(source.url)
      const seg = url.pathname.split('/').filter(Boolean).pop() || ''
      if (!seg) return url.hostname
      return slugToTitleCase(decodeURIComponent(seg))
    } catch {
      return source.url
    }
  }

  async function handleSubmit(submittedQuery: string) {
    if (!submittedQuery.trim()) return

    setHasSubmitted(true)
    setQuery('')
    setError(null)
    setLoading(true)
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), role: 'user', content: submittedQuery },
    ])

    try {
      // Build history payload (including current user text temporarily appended in state view)
      const historyPayload = [...messages, { role: 'user', content: submittedQuery }].map((m) => ({
        role: m.role,
        content: m.content,
      }))
      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: submittedQuery, json: true, chat_history: historyPayload }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const raw = await res.json()
      
      let answerText = (raw?.answer_text ?? raw?.answer ?? raw?.output ?? raw?.text ?? '').toString()
      if (!answerText) answerText = 'No answer text returned.'

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: answerText,
          sources: Array.isArray(raw?.sources) ? raw.sources : [],
          follow_up_questions: Array.isArray(raw?.follow_up_questions) ? raw.follow_up_questions : [],
          generated_sql: raw?.generated_sql || null,
          active_collection: raw?.active_collection || null,
        },
      ])
      
      // Auto-open sidebar if it's a schema query
      if (raw?.active_collection === 'schema') {
        setIsSidebarOpen(true)
      }
    } catch (e: any) {
      setError(e.message || 'An error occurred')
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          role: 'assistant',
          content: `Error: ${e.message || 'An error occurred'}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  // Find latest metadata for sidebar
  const activeInteraction = [...messages].reverse().find(m => m.role === 'assistant')
  const metadataTarget = activeInteraction?.active_collection || 'None'
  const metadataSql = activeInteraction?.generated_sql || ''

  return (
    <div className="h-screen w-full bg-slate-50 flex overflow-hidden font-sans">
      
      {/* Main Content Column */}
      <div className={`flex-1 flex flex-col h-full bg-cover transition-all duration-300 relative ${hasSubmitted && isSidebarOpen ? 'mr-0 md:mr-[360px]' : ''}`}>
        
        {/* Header Bar */}
        <header className="h-16 shrink-0 border-b border-slate-200 bg-white/80 backdrop-blur-md flex items-center justify-between px-6 z-10 sticky top-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-blue-500 flex items-center justify-center text-white font-bold tracking-tighter">
              XR
            </div>
            <h1 className="text-lg font-bold text-slate-800 tracking-tight">XIT-RAG Cognitive Engine</h1>
          </div>
          {hasSubmitted && (
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className={`p-2 rounded-lg border text-sm font-medium transition-colors ${
                isSidebarOpen ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {isSidebarOpen ? 'Hide DB Data' : 'View DB Data'}
              </div>
            </button>
          )}
        </header>

        {/* Scrollable Area */}
        <div className="flex-1 overflow-y-auto relative scroll-smooth bg-slate-50">
          {!hasSubmitted ? (
            // Landing Dashboard
            <div className="min-h-full flex flex-col items-center justify-center px-4 py-16">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-600 via-blue-500 to-sky-400 flex items-center justify-center text-white mb-8 shadow-xl shadow-blue-500/20">
                <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 text-center tracking-tight">
                What can I help you find?
              </h2>
              <p className="text-slate-500 mb-10 text-center max-w-lg text-lg">
                Query both the internal compliance knowledge base and the system database using natural language.
              </p>

              {/* Input for Landing */}
              <div className="w-full max-w-3xl mb-12">
                <div className="relative bg-white rounded-2xl shadow-sm border border-slate-200/60 focus-within:ring-2 focus-within:ring-indigo-500/50 transition-all p-2 flex items-center">
                  <div className="pl-4 pr-2 text-slate-400">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                  </div>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSubmit(query)
                      }
                    }}
                    placeholder="Search documents, policies, database tables, or ask questions..."
                    className="flex-1 outline-none text-slate-800 placeholder-slate-400 text-lg bg-transparent py-3"
                  />
                  <button
                    onClick={() => handleSubmit(query)}
                    disabled={!query.trim()}
                    className="ml-2 text-white bg-indigo-600 hover:bg-indigo-700 px-6 py-3 rounded-xl font-semibold shadow-sm disabled:opacity-40 transition-colors cursor-pointer"
                  >
                    Search
                  </button>
                </div>
              </div>

              {/* Suggestions */}
              <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {SUGGESTION_CHIPS.map((chip, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setQuery(chip.text)
                      handleSubmit(chip.text)
                    }}
                    className={`cursor-pointer group relative overflow-hidden bg-gradient-to-br ${chip.color} text-white p-5 rounded-2xl font-medium text-sm flex items-center gap-3 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all text-left w-full`}
                  >
                    <span>{chip.text}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            // Chat History
            <div className="max-w-4xl w-full mx-auto px-6 py-8 space-y-8 pb-32">
              {messages.map((m) => (
                m.role === 'user' ? (
                  <div className="flex justify-end" key={m.id}>
                    <div className="bg-indigo-600 text-white px-6 py-4 rounded-full rounded-tr-sm max-w-[85%] shadow-sm">
                      <p className="text-base leading-relaxed">{m.content}</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-start" key={m.id}>
                    <div className="bg-white border border-slate-200 px-7 py-6 rounded-3xl rounded-tl-sm max-w-[90%] shadow-sm w-full">
                      <div className="space-y-6">
                        <div className="text-slate-800 text-base leading-relaxed">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              table: ({node, ...props}) => (
                                <div className="overflow-x-auto my-6 rounded-xl border border-slate-200/60 shadow-sm">
                                  <table className="w-full text-sm text-left border-collapse" {...props} />
                                </div>
                              ),
                              thead: ({node, ...props}) => <thead className="bg-slate-50/80 text-slate-700" {...props} />,
                              th: ({node, ...props}) => <th className="px-5 py-3.5 font-semibold border-b border-slate-200/60 uppercase tracking-widest text-[11px]" {...props} />,
                              td: ({node, ...props}) => <td className="px-5 py-4 border-b border-slate-100 last:border-b-0 text-gray-700" {...props} />,
                              p: ({node, ...props}) => <p className="mb-4 last:mb-0 leading-relaxed" {...props} />,
                              ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-4 space-y-2" {...props} />,
                              ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-4 space-y-2" {...props} />,
                              li: ({node, ...props}) => <li className="pl-1" {...props} />,
                              strong: ({node, ...props}) => <strong className="font-bold text-slate-900" {...props} />,
                            }}
                          >
                            {m.content}
                          </ReactMarkdown>
                        </div>
                        
                        {/* Sources Section */}
                        {m.sources && m.sources.length > 0 && (
                          <div className="pt-4 border-t border-slate-100">
                            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-3">Retrieved Citations</h4>
                            <div className="flex flex-wrap gap-2">
                              {(() => {
                                const byUrl = new Map<string, Source>()
                                for (const s of m.sources) {
                                  const link = canonicalizeUrl(s.url)
                                  if (!byUrl.has(link)) byUrl.set(link, { ...s, url: link })
                                }
                                return Array.from(byUrl.values()).map((s, i) => (
                                  <a key={i} href={s.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-medium text-slate-600 hover:text-indigo-600 hover:border-indigo-200 transition-colors">
                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                                    {cleanSourceLabel(s)}
                                  </a>
                                ))
                              })()}
                            </div>
                          </div>
                        )}

                        {/* Follow Up Questions */}
                        {m.follow_up_questions && m.follow_up_questions.length > 0 && (
                          <div className="pt-4 border-t border-slate-100">
                            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-3">Suggested Questions</h4>
                            <div className="flex flex-col gap-2">
                              {m.follow_up_questions.map((q, i) => (
                                <button
                                  key={i}
                                  onClick={() => handleSubmit(q)}
                                  className="cursor-pointer w-full text-left px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 hover:border-indigo-200 transition-colors text-sm font-medium flex items-center gap-3"
                                >
                                  <svg className="w-4 h-4 text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                                  {q}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              ))}
              
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-200 px-6 py-5 rounded-3xl rounded-tl-sm shadow-sm inline-flex items-center gap-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm font-medium text-slate-500">Processing...</span>
                  </div>
                </div>
              )}
              
              {error && (
                <div className="flex justify-start">
                  <div className="text-red-700 bg-red-50 border border-red-200 rounded-xl p-4 shadow-sm">
                    <p className="font-bold text-sm mb-1">System Error</p>
                    <p className="text-sm">{error}</p>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} className="h-4" />
            </div>
          )}
        </div>

        {/* Fixed Chat Input Area (only visible after first submit) */}
        {hasSubmitted && (
          <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent">
            <div className="max-w-4xl mx-auto w-full relative bg-white rounded-2xl shadow-lg border border-slate-200 focus-within:ring-2 focus-within:ring-indigo-500/50 p-2 flex items-center transition-all cursor-text">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    if (query.trim()) handleSubmit(query.trim())
                  }
                }}
                placeholder="Ask a follow up question..."
                className="flex-1 outline-none text-slate-800 placeholder-slate-400 text-base py-2.5 px-4 bg-transparent"
              />
              <button
                onClick={() => query.trim() && handleSubmit(query.trim())}
                disabled={!query.trim() || loading}
                className="text-white bg-indigo-600 hover:bg-indigo-700 px-5 py-2.5 rounded-xl font-semibold disabled:opacity-50 transition-colors ml-2 cursor-pointer"
              >
                Send
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Persistent Right Sidebar */}
      {hasSubmitted && (
        <div 
          className={`fixed inset-y-0 right-0 w-[360px] bg-white border-l border-slate-200 shadow-2xl transform transition-transform duration-300 ease-in-out z-30 flex flex-col ${
            isSidebarOpen ? 'translate-x-0' : 'translate-x-full'
          }`}
        >
          {/* Sidebar Header */}
          <div className="h-16 shrink-0 border-b border-slate-100 flex items-center justify-between px-5 bg-slate-50/50">
            <h3 className="font-bold tracking-tight text-slate-800 flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>
              System Metadata
            </h3>
            <button onClick={() => setIsSidebarOpen(false)} className="cursor-pointer p-1.5 rounded-md hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>

          {/* Sidebar Scrollable Body */}
          <div className="flex-1 overflow-y-auto p-5 bg-white space-y-6">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">Diagnostic Status</p>
              <div className="p-4 rounded-xl border border-indigo-100 bg-indigo-50/50 space-y-4">
                <div>
                  <span className="block text-xs font-semibold text-indigo-400 uppercase tracking-widest mb-1.5">Route Selected</span>
                  <span className="inline-flex px-2.5 py-1 rounded-md bg-indigo-100 text-indigo-700 font-mono text-sm leading-none border border-indigo-200/50">
                    {metadataTarget}
                  </span>
                </div>
                
                {metadataTarget === 'schema' ? (
                  <div className="text-xs text-indigo-600 leading-snug">
                    Query routed to Internal Entity ERD Database. Used CTE generation for database execution via strict retrieval mode.
                  </div>
                ) : (
                  <div className="text-xs text-indigo-600 leading-snug">
                    Query routed to standard vector Knowledge Base context.
                  </div>
                )}
              </div>
            </div>

            {metadataSql && (
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center justify-between">
                  <span>Generated SQL Trace</span>
                  <span className="bg-emerald-100 text-emerald-700 text-[10px] px-2 py-0.5 rounded-full">Exited 0</span>
                </p>
                <div className="relative rounded-xl overflow-hidden shadow-inner border border-slate-800 bg-[#0f172a]">
                  <div className="flex items-center px-4 py-2 border-b border-slate-700/50 bg-slate-900/50">
                    <div className="flex gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-slate-600"></div>
                      <div className="w-2.5 h-2.5 rounded-full bg-slate-600"></div>
                      <div className="w-2.5 h-2.5 rounded-full bg-slate-600"></div>
                    </div>
                  </div>
                  <pre className="p-4 whitespace-pre-wrap break-words text-[13px] font-mono leading-relaxed text-sky-400">
                    <code>{metadataSql}</code>
                  </pre>
                </div>
              </div>
            )}
          </div>
          
          {/* Footer Area */}
          <div className="p-5 border-t border-slate-100 bg-slate-50/50">
             <p className="text-[11px] text-slate-400 leading-tight text-center">
               This metadata panel displays diagnostic traces exclusively for the most recent system interaction.
             </p>
          </div>
        </div>
      )}
    </div>
  )
}
