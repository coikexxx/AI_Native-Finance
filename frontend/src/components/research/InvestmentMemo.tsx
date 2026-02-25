import ReactMarkdown from 'react-markdown'

interface Props {
  memoMd: string
  ticker: string
}

export function InvestmentMemo({ memoMd, ticker }: Props) {
  if (!memoMd) return null

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="section-title">投研报告 Investment Memo — {ticker}</h2>
        <button
          onClick={() => {
            const blob = new Blob([memoMd], { type: 'text/markdown' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `${ticker}_investment_memo.md`
            a.click()
            URL.revokeObjectURL(url)
          }}
          className="btn-ghost text-xs flex items-center gap-1"
          title="Download memo as Markdown"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          导出 Export
        </button>
      </div>

      <div className="memo-content prose prose-invert max-w-none">
        <ReactMarkdown
          components={{
            // Make citation links scroll to evidence panel
            a: ({ href, children, ...props }) => {
              if (href?.startsWith('#E') || (typeof children === 'string' && children.match(/^\[E\d+\]$/))) {
                return (
                  <a
                    href={href}
                    onClick={(e) => {
                      e.preventDefault()
                      const id = href?.replace('#', '')
                      document.getElementById(id || '')?.scrollIntoView({ behavior: 'smooth' })
                    }}
                    className="text-sky-400 hover:text-sky-300 font-mono text-xs"
                    {...props}
                  >
                    {children}
                  </a>
                )
              }
              return <a href={href} target="_blank" rel="noopener noreferrer" {...props}>{children}</a>
            },
          }}
        >
          {memoMd}
        </ReactMarkdown>
      </div>
    </div>
  )
}
