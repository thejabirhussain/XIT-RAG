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

interface CompareModelResponse {
  answer_text: string
  sources: Source[]
  confidence: 'low' | 'medium' | 'high'
  query_embedding_similarity: number[]
  generated_sql?: string | null
  active_collection?: string | null
  db_results?: any[] | null
  total_records?: number | null
  export_id?: string | null
  model_name: string
  elapsed_ms: number
  token_usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  } | null
  prompt_sent?: string | null
  logs?: string | null
}

interface CompareResponse {
  query: string
  responses: {
    llama_7b: CompareModelResponse
    qwen_14b: CompareModelResponse
    qwen_32b: CompareModelResponse
  }
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
  
  // Compare Mode state
  const [compareMode, setCompareMode] = useState(false)
  const [compareLoading, setCompareLoading] = useState(false)
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null)
  const [compareError, setCompareError] = useState<string | null>(null)
  const [compareQuery, setCompareQuery] = useState('')
  const [syncScroll, setSyncScroll] = useState(true)
  const [highlightDiff, setHighlightDiff] = useState(false)
  const [copiedModel, setCopiedModel] = useState<string | null>(null)

  // Sidebar state
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  // Scroll Refs
  const chatEndRef = useRef<HTMLDivElement>(null)
  const colLlamaRef = useRef<HTMLDivElement>(null)
  const colQwen14Ref = useRef<HTMLDivElement>(null)
  const colQwen32Ref = useRef<HTMLDivElement>(null)
  const isSyncing = useRef(false)
  
  useEffect(() => {
    if (!compareMode && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading, compareMode])

  // Synchronized scroll listener
  const handleScroll = (sourceRef: React.RefObject<HTMLDivElement | null>) => {
    if (!syncScroll || isSyncing.current) return
    const source = sourceRef.current
    if (!source) return

    isSyncing.current = true
    const targets = [
      { key: 'llama_7b', ref: colLlamaRef },
      { key: 'qwen_14b', ref: colQwen14Ref },
      { key: 'qwen_32b', ref: colQwen32Ref }
    ].filter(t => t.ref !== sourceRef)

    targets.forEach(t => {
      const target = t.ref.current
      if (target) {
        target.scrollTop = source.scrollTop
      }
    })
    
    window.requestAnimationFrame(() => {
      isSyncing.current = false
    })
  }

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
    
    if (compareMode) {
      setCompareQuery(submittedQuery)
      setCompareLoading(true)
      setCompareError(null)
      setCompareResult(null)

      try {
        const res = await fetch('/query/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: submittedQuery }),
        })

        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)

        const data = await res.json()
        setCompareResult(data)
      } catch (e: any) {
        setCompareError(e.message || 'An error occurred during multi-model comparison')
      } finally {
        setCompareLoading(false)
      }
    } else {
      setLoading(true)
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: 'user', content: submittedQuery },
      ])

      try {
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
  }

  // Copy helper
  const handleCopy = (text: string, modelKey: string) => {
    navigator.clipboard.writeText(text)
    setCopiedModel(modelKey)
    setTimeout(() => {
      setCopiedModel(null)
    }, 2000)
  }

  // factual similarity visual highlight helper
  function highlightText(text: string, otherTexts: string[]) {
    if (!highlightDiff) return text
    
    // Highlight numbers, dates, currency, percentages
    const regex = /(\b\d+(?:\.\d+)?%?|\$\d+(?:\.\d+)?|\b\d{4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:, \d{4})?)/gi
    const parts = text.split(regex)
    
    return parts.map((part, i) => {
      if (part.match(regex)) {
        const cleanPart = part.trim().toLowerCase()
        const foundInOthers = otherTexts.some(o => o.toLowerCase().includes(cleanPart))
        return (
          <span 
            key={i} 
            className={`px-1 rounded font-semibold transition-all ${
              foundInOthers 
                ? 'bg-amber-100 text-amber-800' 
                : 'bg-rose-100 text-rose-800 border-b-2 border-rose-400'
            }`}
            title={foundInOthers ? 'Value matches other responses' : 'Unique value - potential hallucination risk'}
          >
            {part}
          </span>
        )
      }
      return part
    })
  }

  // Find latest metadata for sidebar (Single Model mode)
  const activeInteraction = [...messages].reverse().find(m => m.role === 'assistant')
  const metadataTarget = activeInteraction?.active_collection || 'None'
  const metadataSql = activeInteraction?.generated_sql || ''

  // Model-specific color themes for styling compare panels
  const modelThemes: Record<string, {
    border: string
    bgLight: string
    badge: string
    accent: string
  }> = {
    llama_7b: {
      border: 'border-purple-200 focus-within:border-purple-400',
      bgLight: 'bg-purple-50/50',
      badge: 'bg-purple-100 text-purple-800 border-purple-200',
      accent: 'text-purple-600'
    },
    qwen_14b: {
      border: 'border-teal-200 focus-within:border-teal-400',
      bgLight: 'bg-teal-50/50',
      badge: 'bg-teal-100 text-teal-800 border-teal-200',
      accent: 'text-teal-600'
    },
    qwen_32b: {
      border: 'border-indigo-200 focus-within:border-indigo-400',
      bgLight: 'bg-indigo-50/50',
      badge: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      accent: 'text-indigo-600'
    }
  }

  return (
    <div className="h-screen w-full bg-slate-50 flex overflow-hidden font-sans">
      
      {/* Main Content Column */}
      <div className={`flex-1 flex flex-col h-full bg-cover transition-all duration-300 relative ${!compareMode && hasSubmitted && isSidebarOpen ? 'mr-0 md:mr-[360px]' : ''}`}>
        
        {/* Header Bar */}
        <header className="h-16 shrink-0 border-b border-slate-200 bg-white/90 backdrop-blur-md flex items-center justify-between px-6 z-10 sticky top-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-blue-500 flex items-center justify-center text-white font-bold tracking-tighter">
              XR
            </div>
            <h1 className="text-lg font-bold text-slate-800 tracking-tight">XIT-RAG Cognitive Engine</h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Compare Models Toggle Switch */}
            <div className="flex items-center gap-2.5 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
              <span className="text-xs font-semibold text-slate-600">Compare Models</span>
              <button 
                onClick={() => {
                  setCompareMode(!compareMode)
                  setHasSubmitted(false)
                  setCompareResult(null)
                  setMessages([])
                }}
                className={`w-10 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors ${
                  compareMode ? 'bg-indigo-600' : 'bg-slate-300'
                }`}
              >
                <div 
                  className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ${
                    compareMode ? 'translate-x-4' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {hasSubmitted && !compareMode && (
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
          </div>
        </header>

        {/* Scrollable Area */}
        <div className="flex-1 overflow-hidden relative bg-slate-50 flex flex-col">
          {!hasSubmitted ? (
            // Landing Dashboard
            <div className="min-h-full overflow-y-auto flex flex-col items-center justify-center px-4 py-16">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-600 via-blue-500 to-sky-400 flex items-center justify-center text-white mb-8 shadow-xl shadow-blue-500/20">
                <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 text-center tracking-tight">
                {compareMode ? 'Multi-Model Comparative RAG' : 'What can I help you find?'}
              </h2>
              <p className="text-slate-500 mb-10 text-center max-w-lg text-lg">
                {compareMode 
                  ? 'Evaluate and compare Llama 7B, Qwen 14B, and Qwen 32B responses side-by-side on the same query.'
                  : 'Query both the internal compliance knowledge base and the system database using natural language.'}
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
                    placeholder={compareMode ? "Enter query to run against all 3 models..." : "Search documents, policies, database tables, or ask questions..."}
                    className="flex-1 outline-none text-slate-800 placeholder-slate-400 text-lg bg-transparent py-3"
                  />
                  <button
                    onClick={() => handleSubmit(query)}
                    disabled={!query.trim()}
                    className="ml-2 text-white bg-indigo-600 hover:bg-indigo-700 px-6 py-3 rounded-xl font-semibold shadow-sm disabled:opacity-40 transition-colors cursor-pointer"
                  >
                    {compareMode ? 'Compare' : 'Search'}
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
          ) : compareMode ? (
            // ==========================================
            // COMPARE MODE VIEW
            // ==========================================
            <div className="flex-1 flex flex-col h-full overflow-hidden">
              {/* Compare Mode Header Settings */}
              <div className="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between shrink-0 shadow-sm z-10">
                <div className="flex items-center gap-2 max-w-[50%]">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Query:</span>
                  <span className="text-sm font-semibold text-slate-700 truncate" title={compareQuery}>{compareQuery}</span>
                </div>
                
                <div className="flex items-center gap-5">
                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-600 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={syncScroll}
                      onChange={(e) => setSyncScroll(e.target.checked)}
                      className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
                    />
                    Synchronized Scrolling
                  </label>
                  
                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-600 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={highlightDiff}
                      onChange={(e) => setHighlightDiff(e.target.checked)}
                      className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
                    />
                    Highlight Fact Discrepancies
                  </label>
                </div>
              </div>

              {compareLoading ? (
                // Shimmer Loading State
                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-200 bg-white overflow-hidden">
                  <SkeletonLoader title="Llama 7B (Groq)" />
                  <SkeletonLoader title="Qwen 14B (Gemini/Groq)" />
                  <SkeletonLoader title="Qwen 32B (Groq)" />
                </div>
              ) : compareError ? (
                <div className="flex-1 flex items-center justify-center p-8 bg-white">
                  <div className="max-w-md text-center p-6 border border-red-200 bg-red-50 rounded-2xl">
                    <h3 className="font-bold text-red-800 text-lg mb-2">Evaluation Query Failed</h3>
                    <p className="text-sm text-red-600">{compareError}</p>
                    <button 
                      onClick={() => handleSubmit(compareQuery)}
                      className="mt-4 px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-semibold hover:bg-red-700 transition-colors cursor-pointer"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              ) : compareResult ? (
                // Evaluation Side-by-Side Panels
                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-200 overflow-hidden bg-slate-50">
                  {/* Panel 1: Llama 7B */}
                  {renderCompareColumn('llama_7b', colLlamaRef)}
                  {/* Panel 2: Qwen 14B */}
                  {renderCompareColumn('qwen_14b', colQwen14Ref)}
                  {/* Panel 3: Qwen 32B */}
                  {renderCompareColumn('qwen_32b', colQwen32Ref)}
                </div>
              ) : null}
            </div>
          ) : (
            // ==========================================
            // DEFAULT CHAT VIEW
            // ==========================================
            <div className="flex-1 overflow-y-auto relative scroll-smooth bg-slate-50">
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
            </div>
          )}
        </div>

        {/* Fixed Chat Input Area (only visible after first submit) */}
        {hasSubmitted && (
          <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent z-10">
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
                placeholder={compareMode ? "Enter another comparison query..." : "Ask a follow up question..."}
                className="flex-1 outline-none text-slate-800 placeholder-slate-400 text-base py-2.5 px-4 bg-transparent"
              />
              <button
                onClick={() => query.trim() && handleSubmit(query.trim())}
                disabled={!query.trim() || loading || compareLoading}
                className="text-white bg-indigo-600 hover:bg-indigo-700 px-5 py-2.5 rounded-xl font-semibold disabled:opacity-50 transition-colors ml-2 cursor-pointer"
              >
                {compareMode ? 'Compare' : 'Send'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Persistent Right Sidebar (Only for Single Model mode) */}
      {hasSubmitted && !compareMode && (
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

  // Sub-component: Model comparison column
  function renderCompareColumn(modelKey: 'llama_7b' | 'qwen_14b' | 'qwen_32b', ref: React.RefObject<HTMLDivElement | null>) {
    if (!compareResult) return null
    const modelData = compareResult.responses[modelKey]
    if (!modelData) return null

    const theme = modelThemes[modelKey]
    
    // Gather all other responses' text for highlighting diffs
    const otherTexts = Object.entries(compareResult.responses)
      .filter(([k]) => k !== modelKey)
      .map(([, data]) => data?.answer_text || '')

    const formattedAnswer = highlightDiff 
      ? highlightText(modelData.answer_text, otherTexts)
      : modelData.answer_text

    return (
      <div className="flex flex-col h-full overflow-hidden bg-white">
        {/* Column Header */}
        <div className={`p-4 border-b border-slate-200 ${theme.bgLight} flex items-center justify-between shrink-0`}>
          <div>
            <h3 className="font-bold text-slate-800 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${modelKey === 'llama_7b' ? 'bg-purple-600' : modelKey === 'qwen_14b' ? 'bg-teal-600' : 'bg-indigo-600'}`} />
              {modelData.model_name}
            </h3>
            <span className="text-[10px] text-slate-400 font-mono tracking-tight block mt-0.5">
              Engine Latency: {modelData.elapsed_ms}ms
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Tokens badge */}
            {modelData.token_usage && (
              <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">
                {modelData.token_usage.total_tokens}T
              </span>
            )}
            {/* Copy Button */}
            <button
              onClick={() => handleCopy(modelData.answer_text, modelKey)}
              className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition-all cursor-pointer"
              title="Copy answer"
            >
              {copiedModel === modelKey ? (
                <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
              )}
            </button>
          </div>
        </div>

        {/* Scrollable Column Body */}
        <div 
          ref={ref}
          onScroll={() => handleScroll(ref)}
          className="flex-1 overflow-y-auto p-5 space-y-6 pb-28 scrollbar-thin"
        >
          {/* Confidence Badge */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Response Confidence</span>
            <span className={`text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full border ${
              modelData.confidence === 'high' 
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                : modelData.confidence === 'medium' 
                ? 'bg-amber-50 text-amber-700 border-amber-200' 
                : 'bg-rose-50 text-rose-700 border-rose-200'
            }`}>
              {modelData.confidence}
            </span>
          </div>

          {/* Model Answer Body */}
          <div className="text-slate-800 text-sm leading-relaxed prose prose-slate max-w-none">
            {highlightDiff ? (
              <p className="whitespace-pre-wrap leading-relaxed">{formattedAnswer as any}</p>
            ) : (
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({node, ...props}) => (
                    <div className="overflow-x-auto my-4 rounded-xl border border-slate-200/60 shadow-sm">
                      <table className="w-full text-xs text-left border-collapse" {...props} />
                    </div>
                  ),
                  thead: ({node, ...props}) => <thead className="bg-slate-50 text-slate-700" {...props} />,
                  th: ({node, ...props}) => <th className="px-4 py-2.5 font-semibold border-b border-slate-200/60 uppercase tracking-widest text-[9px]" {...props} />,
                  td: ({node, ...props}) => <td className="px-4 py-3 border-b border-slate-100 last:border-b-0 text-gray-700" {...props} />,
                  p: ({node, ...props}) => <p className="mb-3 last:mb-0 leading-relaxed" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-3 space-y-1" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-3 space-y-1" {...props} />,
                  li: ({node, ...props}) => <li className="pl-0.5" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-bold text-slate-900" {...props} />,
                }}
              >
                {modelData.answer_text}
              </ReactMarkdown>
            )}
          </div>

          {/* Collapsible Details Sections */}
          <div className="pt-4 border-t border-slate-100 space-y-3">
            {/* 1. Retrieved Chunks/Collections */}
            {modelData.sources && modelData.sources.length > 0 && (
              <details className="group border border-slate-200/60 rounded-xl overflow-hidden transition-all bg-slate-50">
                <summary className="cursor-pointer p-3 text-xs font-semibold text-slate-600 flex items-center justify-between hover:bg-slate-100/70 select-none">
                  <span>Retrieved Chunks ({modelData.sources.length})</span>
                  <svg className="w-3.5 h-3.5 transform transition-transform group-open:rotate-180 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                </summary>
                <div className="p-3 border-t border-slate-200/60 bg-white space-y-3 text-xs">
                  {modelData.sources.map((s, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg border border-slate-100 bg-slate-50/50">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-semibold text-slate-700 truncate max-w-[70%]" title={s.title}>
                          {s.title || 'Source Citation'}
                        </span>
                        <span className="text-[10px] bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded font-mono">
                          Sim: {s.score.toFixed(3)}
                        </span>
                      </div>
                      {s.section && (
                        <p className="text-[10px] text-slate-400 mb-1 font-medium">{s.section}</p>
                      )}
                      <p className="text-slate-500 italic leading-normal line-clamp-3 bg-white p-2 rounded border border-slate-100">
                        "{s.snippet}"
                      </p>
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-[10px] text-indigo-600 hover:underline mt-2 inline-block font-medium">
                        Open Original Resource
                      </a>
                    </div>
                  ))}
                </div>
              </details>
            )}

            {/* 2. Generated SQL Query */}
            {modelData.generated_sql && (
              <details className="group border border-slate-200/60 rounded-xl overflow-hidden transition-all bg-slate-50">
                <summary className="cursor-pointer p-3 text-xs font-semibold text-slate-600 flex items-center justify-between hover:bg-slate-100/70 select-none">
                  <span>Generated SQL Statement</span>
                  <svg className="w-3.5 h-3.5 transform transition-transform group-open:rotate-180 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                </summary>
                <div className="p-3 border-t border-slate-200/60 bg-[#0f172a] text-[#38bdf8] font-mono text-[11px] whitespace-pre-wrap break-all shadow-inner leading-relaxed">
                  <code>{modelData.generated_sql}</code>
                </div>
              </details>
            )}

            {/* 3. Prompt Sent to Model */}
            {modelData.prompt_sent && (
              <details className="group border border-slate-200/60 rounded-xl overflow-hidden transition-all bg-slate-50">
                <summary className="cursor-pointer p-3 text-xs font-semibold text-slate-600 flex items-center justify-between hover:bg-slate-100/70 select-none">
                  <span>Prompt Sent to Model</span>
                  <svg className="w-3.5 h-3.5 transform transition-transform group-open:rotate-180 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                </summary>
                <div className="p-3 border-t border-slate-200/60 bg-slate-900 text-slate-300 font-mono text-[10px] whitespace-pre-wrap max-h-60 overflow-y-auto leading-relaxed shadow-inner">
                  <code>{modelData.prompt_sent}</code>
                </div>
              </details>
            )}

            {/* 4. Model Logs & SQL Trace */}
            {modelData.logs && (
              <details className="group border border-slate-200/60 rounded-xl overflow-hidden transition-all bg-slate-50">
                <summary className="cursor-pointer p-3 text-xs font-semibold text-slate-600 flex items-center justify-between hover:bg-slate-100/70 select-none">
                  <span>Execution Logs & Trace</span>
                  <svg className="w-3.5 h-3.5 transform transition-transform group-open:rotate-180 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                </summary>
                <div className="p-3 border-t border-slate-200/60 bg-slate-950 text-emerald-400 font-mono text-[10px] whitespace-pre-wrap max-h-60 overflow-y-auto leading-normal">
                  <code>{modelData.logs}</code>
                </div>
              </details>
            )}
          </div>
        </div>
      </div>
    )
  }
}

// Shimmer Loader Column Component
function SkeletonLoader({ title }: { title: string }) {
  return (
    <div className="flex flex-col h-full bg-white overflow-hidden p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 shrink-0">
        <div>
          <h3 className="font-bold text-slate-700">{title}</h3>
          <div className="h-3 w-24 bg-slate-200 rounded animate-pulse mt-1"></div>
        </div>
        <div className="h-7 w-7 bg-slate-100 rounded-lg animate-pulse"></div>
      </div>
      
      <div className="flex-1 space-y-4 overflow-hidden">
        <div className="flex justify-between items-center">
          <div className="h-3 w-28 bg-slate-100 rounded animate-pulse"></div>
          <div className="h-5 w-14 bg-slate-200 rounded-full animate-pulse"></div>
        </div>
        <div className="space-y-2.5 pt-2">
          <div className="h-4 w-full bg-slate-200 rounded animate-pulse"></div>
          <div className="h-4 w-11/12 bg-slate-200 rounded animate-pulse"></div>
          <div className="h-4 w-5/6 bg-slate-200 rounded animate-pulse"></div>
          <div className="h-4 w-full bg-slate-200 rounded animate-pulse"></div>
          <div className="h-4 w-4/5 bg-slate-200 rounded animate-pulse"></div>
        </div>
      </div>
    </div>
  )
}
