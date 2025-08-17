'use client'

import { useState } from 'react'
import { Upload, FileText, Link, Loader2, Copy, Download, Info, CheckCircle, AlertCircle, HelpCircle, XCircle, Mail, FileUp, DollarSign, Users, Calendar, Coffee } from 'lucide-react'

interface QuoteData {
  total_quote: {
    status: 'explicit' | 'derived' | 'conditional' | 'not_found'
    value: number | null
    currency: string
    provenance_snippet: string | null
    notes: string
  }
  guestroom_total: {
    status: 'explicit' | 'derived' | 'conditional' | 'not_found'
    value: number | null
    currency: string
    provenance_snippet: string | null
    notes: string
  }
  meeting_room_total: {
    status: 'explicit' | 'derived' | 'conditional' | 'not_found'
    value: number | null
    currency: string
    provenance_snippet: string | null
    notes: string
  }
  fnb_total: {
    status: 'explicit' | 'derived' | 'conditional' | 'not_found'
    value: number | null
    currency: string
    provenance_snippet: string | null
    notes: string
  }
  extras: {
    room_nights: number | null
    nightly_rate: number | null
    tax_rate_pct: number | null
    service_rate_pct: number | null
    fnb_minimum: number | null
    proposal_url: string | null
    guestroom_base: number | null
    guestroom_taxes_fees: number | null
    estimated_fnb_gross: number | null
    effective_value_offsets: string[]
  }
  property?: any
  program?: any
  concessions?: string[]
  policies?: any
  sources?: string[]
}

interface TotalCardProps {
  title: string
  value: number | null
  status: string
  icon: React.ReactNode
  subtitle?: string | null
  breakdown?: string | null
  provenance?: string | null
  conditions?: string[]
}

function TotalCard({ title, value, status, icon, subtitle, breakdown, provenance, conditions }: TotalCardProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'explicit': return 'bg-emerald-50 border-emerald-200 text-emerald-700'
      case 'derived': return 'bg-blue-50 border-blue-200 text-blue-700'
      case 'conditional': return 'bg-amber-50 border-amber-200 text-amber-700'
      case 'not_found': return 'bg-gray-50 border-gray-200 text-gray-600'
      default: return 'bg-gray-50 border-gray-200 text-gray-600'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'explicit': return 'Explicit'
      case 'derived': return 'Calculated'
      case 'conditional': return 'Conditional'
      case 'not_found': return 'Not Found'
      default: return 'Unknown'
    }
  }

  const getDisplayValue = () => {
    if (value !== null) {
      return money(value)
    }
    if (status === 'not_found') {
      return '—'
    }
    return '—'
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-all duration-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gray-50 rounded-lg">
            {icon}
          </div>
          <div>
            <h3 className="font-medium text-gray-900 text-base">{title}</h3>
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(status)}`}>
              {getStatusText(status)}
            </span>
          </div>
        </div>
        
        {/* Tooltip Button */}
        {provenance && (
          <button
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <Info className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Main Value */}
      <div className="mb-3">
        <div className="text-2xl font-light text-gray-900">
          {getDisplayValue()}
        </div>
      </div>

      {/* Subtitle */}
      {subtitle && (
        <p className="text-sm text-gray-600 mb-3 font-light">
          {subtitle}
        </p>
      )}

      {/* Breakdown */}
      {breakdown && (
        <div className="bg-gray-50 rounded-lg p-3 mb-3">
          <p className="text-sm text-gray-700 font-light leading-relaxed">
            {breakdown}
          </p>
        </div>
      )}

      {/* Conditions */}
      {conditions && conditions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {conditions.map((condition, index) => (
            <span key={index} className="px-2 py-1 bg-amber-50 text-amber-700 text-xs rounded-md border border-amber-200 font-light">
              {condition}
            </span>
          ))}
        </div>
      )}

      {/* Tooltip */}
      {showTooltip && provenance && (
        <div className="absolute z-10 mt-2 p-3 bg-gray-900 text-white text-sm rounded-lg shadow-lg max-w-xs">
          <div className="font-medium mb-1">Source:</div>
          <div className="font-light leading-relaxed">{provenance}</div>
          <div className="absolute top-0 left-4 transform -translate-y-1/2 w-2 h-2 bg-gray-900 rotate-45"></div>
        </div>
      )}
    </div>
  )
}

interface DetailCardProps {
  title: string
  children: React.ReactNode
  className?: string
}

function DetailCard({ title, children, className = '' }: DetailCardProps) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 shadow-sm ${className}`}>
      <h3 className="font-medium text-gray-900 mb-4 text-base">{title}</h3>
      <div className="space-y-3">
        {children}
      </div>
    </div>
  )
}

function money(amount: number | null): string {
  if (amount === null) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
}

function downloadCSV(quoteData: QuoteData) {
  const csvContent = [
    ['Field', 'Value', 'Status', 'Notes'],
    ['Total Quote', quoteData.total_quote.value || '', quoteData.total_quote.status, quoteData.total_quote.notes],
    ['Guestroom Total', quoteData.guestroom_total.value || '', quoteData.guestroom_total.status, quoteData.guestroom_total.notes],
    ['Meeting Room Total', quoteData.meeting_room_total.value || '', quoteData.meeting_room_total.status, quoteData.meeting_room_total.notes],
    ['F&B Total', quoteData.fnb_total.value || '', quoteData.fnb_total.status, quoteData.fnb_total.notes],
  ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'hotel-quote-data.csv'
  a.click()
  window.URL.revokeObjectURL(url)
}

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [quoteData, setQuoteData] = useState<QuoteData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [urls, setUrls] = useState<string[]>([])
  const [sources, setSources] = useState<string[]>([])

  // Dual input state
  const [emailContent, setEmailContent] = useState('')
  const [emailFile, setEmailFile] = useState<File | null>(null)
  const [proposalFile, setProposalFile] = useState<File | null>(null)
  const [proposalUrl, setProposalUrl] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    console.log('=== Frontend: Form submitted ===')
    console.log('Email content length:', emailContent.length)
    console.log('Email file:', emailFile?.name, emailFile?.size, emailFile?.type)
    console.log('Proposal file:', proposalFile?.name, proposalFile?.size, proposalFile?.type)
    console.log('Proposal URL:', proposalUrl)
    
    setIsLoading(true)
    setError(null)
    setQuoteData(null)
    setUrls([])
    setSources([])

    try {
      const formData = new FormData()
      
      // Add email content (text or file)
      if (emailContent.trim()) {
        console.log('Adding email content to form data')
        formData.append('email_content', emailContent)
      }
      if (emailFile) {
        console.log('Adding email file to form data:', emailFile.name)
        formData.append('email_file', emailFile)
      }
      
      // Add proposal content (file or URL)
      if (proposalFile) {
        console.log('Adding proposal file to form data:', proposalFile.name)
        formData.append('proposal_file', proposalFile)
      }
      if (proposalUrl.trim()) {
        console.log('Adding proposal URL to form data:', proposalUrl)
        formData.append('proposal_url', proposalUrl)
      }

      console.log('Sending request to /api/process...')
      const response = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      })

      console.log('Response status:', response.status)
      const result = await response.json()
      console.log('Response data:', result)

      if (result.success) {
        setQuoteData(result.data)
        setUrls(result.urls_found || [])
        setSources(result.sources || [])
      } else {
        setError(result.error || 'Failed to process request')
      }
    } catch (err) {
      console.error('Error:', err)
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  const getTotalQuoteSubtitle = () => {
    if (!quoteData) return null
    if (quoteData.total_quote.status === 'not_found') {
      return 'Hotel did not provide an all-in total.'
    }
    return null
  }

  const getCalculatedTotalQuote = () => {
    if (!quoteData) return null
    
    const guestroom = quoteData.guestroom_total.value || 0
    const meeting = quoteData.meeting_room_total.value || 0
    const fnb = quoteData.extras?.estimated_fnb_gross || quoteData.fnb_total.value || 0
    
    return guestroom + meeting + fnb
  }

  const getGuestroomBreakdown = () => {
    if (!quoteData?.extras) return null
    const { room_nights, nightly_rate, guestroom_base, guestroom_taxes_fees } = quoteData.extras
    if (room_nights && nightly_rate) {
      const base = room_nights * nightly_rate
      const taxes = guestroom_taxes_fees || 0
      return `${room_nights} room-nights × $${nightly_rate} = $${money(base)}; +${money(taxes)} taxes & fees.`
    }
    return null
  }

  const getFnbBreakdown = () => {
    if (!quoteData?.extras) return null
    const { fnb_minimum, service_rate_pct, tax_rate_pct, estimated_fnb_gross } = quoteData.extras
    if (estimated_fnb_gross) {
      return `F&B Minimum: ${money(fnb_minimum || 0)}; Service Charge (${service_rate_pct || 0}%): ${money((fnb_minimum || 0) * (service_rate_pct || 0) / 100)}; Tax on Service Charge (${tax_rate_pct || 0}%): ${money(((fnb_minimum || 0) * (service_rate_pct || 0) / 100) * (tax_rate_pct || 0) / 100)}; Tax on F&B (${tax_rate_pct || 0}%): ${money((fnb_minimum || 0) * (tax_rate_pct || 0) / 100)}; Total: ${money(estimated_fnb_gross)}`
    }
    return null
  }

  const getMeetingRoomConditions = () => {
    if (!quoteData) return []
    if (quoteData.meeting_room_total.status === 'conditional') {
      // Use the actual provenance snippet or notes from the data
      const condition = quoteData.meeting_room_total.provenance_snippet || 
                       quoteData.meeting_room_total.notes ||
                       'Conditional on F&B minimum'
      return [condition]
    }
    return []
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-light text-gray-900">Hotel Quote Parser</h1>
              <p className="text-gray-600 mt-1 font-light">Extract structured data from hotel proposals and emails</p>
            </div>
            {quoteData && (
              <div className="flex space-x-2">
                <button
                  onClick={() => copyToClipboard(JSON.stringify(quoteData, null, 2))}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copy JSON
                </button>
                <button
                  onClick={() => downloadCSV(quoteData)}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download CSV
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Section */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm sticky top-8">
              <h2 className="text-xl font-medium text-gray-900 mb-6">Upload Content</h2>
              
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Email Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Content
                  </label>
                  <div className="space-y-3">
                    <textarea
                      value={emailContent}
                      onChange={(e) => setEmailContent(e.target.value)}
                      placeholder="Paste email content here..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none font-light"
                      rows={4}
                    />
                    <div className="relative">
                      <input
                        type="file"
                        onChange={(e) => setEmailFile(e.target.files?.[0] || null)}
                        accept=".pdf,.html,.htm,.txt"
                        className="hidden"
                        id="email-file"
                      />
                      <label
                        htmlFor="email-file"
                        className="flex items-center justify-center w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer"
                      >
                        <Mail className="w-4 h-4 mr-2" />
                        Upload Email File
                      </label>
                    </div>
                    {emailFile && (
                      <div className="text-sm text-gray-600 font-light">
                        Selected: {emailFile.name}
                      </div>
                    )}
                  </div>
                </div>

                {/* Proposal Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Proposal
                  </label>
                  <div className="space-y-3">
                    <input
                      type="url"
                      value={proposalUrl}
                      onChange={(e) => setProposalUrl(e.target.value)}
                      placeholder="Proposal URL (optional)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-light"
                    />
                    <div className="relative">
                      <input
                        type="file"
                        onChange={(e) => setProposalFile(e.target.files?.[0] || null)}
                        accept=".pdf,.html,.htm"
                        className="hidden"
                        id="proposal-file"
                      />
                      <label
                        htmlFor="proposal-file"
                        className="flex items-center justify-center w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer"
                      >
                        <FileUp className="w-4 h-4 mr-2" />
                        Upload Proposal File
                      </label>
                    </div>
                    {proposalFile && (
                      <div className="text-sm text-gray-600 font-light">
                        Selected: {proposalFile.name}
                      </div>
                    )}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || (!emailContent && !emailFile && !proposalFile && !proposalUrl)}
                  className="w-full flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Extract Quote Data
                    </>
                  )}
                </button>
              </form>

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-800 font-light">{error}</p>
                </div>
              )}
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2">
            {quoteData ? (
              <div className="space-y-6">
                {/* Status Bar */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                    <span className="text-green-800 font-medium">
                      Processed from: {sources.join(', ')}
                    </span>
                  </div>
                  {urls.length > 0 && (
                    <div className="mt-2 text-sm text-green-700 font-light">
                      URLs found: {urls.length}
                    </div>
                  )}
                </div>

                {/* Total Amounts - Prominent Display */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <TotalCard
                    title="Total Quote"
                    value={getCalculatedTotalQuote()}
                    status={quoteData.total_quote.status}
                    icon={<DollarSign className="w-5 h-5 text-gray-600" />}
                    subtitle={getTotalQuoteSubtitle()}
                    provenance={quoteData.total_quote.provenance_snippet}
                  />
                  <TotalCard
                    title="Guestroom Total"
                    value={quoteData.guestroom_total.value}
                    status={quoteData.guestroom_total.status}
                    icon={<Users className="w-5 h-5 text-gray-600" />}
                    breakdown={getGuestroomBreakdown()}
                    provenance={quoteData.guestroom_total.provenance_snippet}
                  />
                  <TotalCard
                    title="Meeting Room Total"
                    value={quoteData.meeting_room_total.value}
                    status={quoteData.meeting_room_total.status}
                    icon={<Calendar className="w-5 h-5 text-gray-600" />}
                    conditions={getMeetingRoomConditions()}
                    provenance={quoteData.meeting_room_total.provenance_snippet}
                  />
                  <TotalCard
                    title="Food & Beverage Total"
                    value={quoteData.extras?.estimated_fnb_gross || quoteData.fnb_total.value}
                    status={quoteData.fnb_total.status}
                    icon={<Coffee className="w-5 h-5 text-gray-600" />}
                    breakdown={getFnbBreakdown()}
                    provenance={quoteData.fnb_total.provenance_snippet}
                  />
                </div>

                {/* Additional Information */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Concessions */}
                  {quoteData.concessions && quoteData.concessions.length > 0 && (
                    <DetailCard title="Concessions" className="lg:col-span-2">
                      <div className="space-y-2">
                        {quoteData.concessions.map((concession, index) => (
                          <div 
                            key={index} 
                            className="p-3 bg-green-50 border border-green-200 rounded-lg"
                          >
                            <p className="text-sm text-green-800 font-light leading-relaxed">
                              {concession}
                            </p>
                          </div>
                        ))}
                      </div>
                    </DetailCard>
                  )}

                  {/* Property Details */}
                  {quoteData.property && Object.keys(quoteData.property).length > 0 && (
                    <DetailCard title="Property Details">
                      <div className="space-y-2 text-sm text-gray-700">
                        {Object.entries(quoteData.property).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="font-medium capitalize">{key.replace(/_/g, ' ')}:</span>
                            <span className="text-right break-words font-light">{String(value || '')}</span>
                          </div>
                        ))}
                      </div>
                    </DetailCard>
                  )}

                  {/* Program Details */}
                  {quoteData.program && Object.keys(quoteData.program).length > 0 && (
                    <DetailCard title="Program Details">
                      <div className="space-y-2 text-sm text-gray-700">
                        {Object.entries(quoteData.program).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="font-medium capitalize">{key.replace(/_/g, ' ')}:</span>
                            <span className="text-right break-words font-light">{String(value || '')}</span>
                          </div>
                        ))}
                      </div>
                    </DetailCard>
                  )}

                  {/* Extras */}
                  {quoteData.extras && (
                    <DetailCard title="Additional Details" className="lg:col-span-2">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        {quoteData.extras.room_nights && (
                          <div>
                            <span className="font-medium text-gray-700">Room Nights:</span>
                            <div className="text-gray-900 font-light">{quoteData.extras.room_nights}</div>
                          </div>
                        )}
                        {quoteData.extras.nightly_rate && (
                          <div>
                            <span className="font-medium text-gray-700">Nightly Rate:</span>
                            <div className="text-gray-900 font-light">{money(quoteData.extras.nightly_rate)}</div>
                          </div>
                        )}
                        {quoteData.extras.tax_rate_pct && (
                          <div>
                            <span className="font-medium text-gray-700">Tax Rate:</span>
                            <div className="text-gray-900 font-light">{quoteData.extras.tax_rate_pct}%</div>
                          </div>
                        )}
                        {quoteData.extras.service_rate_pct && (
                          <div>
                            <span className="font-medium text-gray-700">Service Rate:</span>
                            <div className="text-gray-900 font-light">{quoteData.extras.service_rate_pct}%</div>
                          </div>
                        )}
                        {quoteData.extras.fnb_minimum && (
                          <div>
                            <span className="font-medium text-gray-700">F&B Minimum:</span>
                            <div className="text-gray-900 font-light">{money(quoteData.extras.fnb_minimum)}</div>
                          </div>
                        )}
                        {quoteData.extras.estimated_fnb_gross && (
                          <div>
                            <span className="font-medium text-gray-700">Est. F&B Gross:</span>
                            <div className="text-gray-900 font-light">{money(quoteData.extras.estimated_fnb_gross)}</div>
                          </div>
                        )}
                      </div>
                    </DetailCard>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Extracted</h3>
                <p className="text-gray-600 font-light">
                  Upload a hotel quote or email to extract structured data
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
