import { NextRequest, NextResponse } from 'next/server'

// Microservice configuration
const MICROSERVICE_URL = process.env.MICROSERVICE_URL || 'http://localhost:8000'

interface MicroserviceResponse {
  success: boolean
  data?: any
  error?: string
  sources: string[]
  urls_found: string[]
}

export async function POST(request: NextRequest) {
  console.log('=== Next.js API: Processing request ===')
  
  try {
    const formData = await request.formData()
    console.log('FormData received, checking contents...')
    
    // Log all form data keys
    const formKeys = Array.from(formData.keys())
    console.log('Form data keys:', formKeys)
    
    // Prepare data for microservice
    const microserviceFormData = new FormData()
    
    // Handle email content (text input)
    const emailContent = formData.get('email_content') as string
    if (emailContent) {
      console.log('Found email content:', emailContent.substring(0, 100) + '...')
      microserviceFormData.append('email_content', emailContent)
    } else {
      console.log('No email content provided')
    }
    
    // Handle email file
    const emailFile = formData.get('email_file') as File
    if (emailFile) {
      console.log('Found email file:', emailFile.name, 'Size:', emailFile.size, 'Type:', emailFile.type)
      microserviceFormData.append('email_file', emailFile)
    } else {
      console.log('No email file provided')
    }
    
    // Handle proposal file
    const proposalFile = formData.get('proposal_file') as File
    if (proposalFile) {
      console.log('Found proposal file:', proposalFile.name, 'Size:', proposalFile.size, 'Type:', proposalFile.type)
      microserviceFormData.append('proposal_file', proposalFile)
    } else {
      console.log('No proposal file provided')
    }
    
    // Handle proposal URL
    const proposalUrl = formData.get('proposal_url') as string
    if (proposalUrl) {
      console.log('Found proposal URL:', proposalUrl)
      microserviceFormData.append('proposal_url', proposalUrl)
    } else {
      console.log('No proposal URL provided')
    }
    
    // Handle legacy single file upload (for backward compatibility)
    const legacyFile = formData.get('file') as File
    if (legacyFile && !proposalFile && !emailFile) {
      console.log('Found legacy file:', legacyFile.name, 'Size:', legacyFile.size, 'Type:', legacyFile.type)
      // If it's a PDF, treat as proposal; if HTML, treat as email
      if (legacyFile.type === 'application/pdf') {
        console.log('Treating legacy file as proposal (PDF)')
        microserviceFormData.append('proposal_file', legacyFile)
      } else {
        console.log('Treating legacy file as email (HTML/text)')
        microserviceFormData.append('email_file', legacyFile)
      }
    } else {
      console.log('No legacy file or already have specific files')
    }
    
    if (!emailContent && !emailFile && !proposalFile && !proposalUrl && !legacyFile) {
      console.log('ERROR: No content provided for extraction')
      return NextResponse.json({ error: 'No content provided for extraction' }, { status: 400 })
    }

    console.log('Calling microservice with sources:', {
      hasEmailContent: !!emailContent,
      hasEmailFile: !!emailFile,
      hasProposalFile: !!proposalFile,
      hasProposalUrl: !!proposalUrl,
      hasLegacyFile: !!legacyFile
    })

    console.log('Microservice URL:', MICROSERVICE_URL)
    console.log('Sending request to microservice...')

    // Call the microservice
    const response = await fetch(`${MICROSERVICE_URL}/extract`, {
      method: 'POST',
      body: microserviceFormData,
    })

    console.log('Microservice response status:', response.status)
    console.log('Microservice response headers:', Object.fromEntries(response.headers.entries()))

    if (!response.ok) {
      const errorText = await response.text()
      console.log('Microservice error response:', errorText)
      throw new Error(`Microservice error: ${response.status} - ${errorText}`)
    }

    const result: MicroserviceResponse = await response.json()
    console.log('Microservice response data:', JSON.stringify(result, null, 2))
    
    if (!result.success) {
      console.log('Microservice returned success: false')
      return NextResponse.json({ error: result.error }, { status: 500 })
    }

    // Transform microservice response to our expected format
    console.log('Transforming microservice response...')
    const transformedData = transformMicroserviceResponse(result.data)
    console.log('Transformed data:', JSON.stringify(transformedData, null, 2))
    
    console.log('=== Next.js API: Processing completed successfully ===')
    
    return NextResponse.json({
      success: true,
      data: transformedData,
      sources: result.sources,
      urls_found: result.urls_found
    })

  } catch (error) {
    console.error('=== Next.js API: Processing error ===', error)
    return NextResponse.json(
      { error: 'Failed to process content' },
      { status: 500 }
    )
  }
}

function transformMicroserviceResponse(microserviceData: any) {
  console.log('Transforming microservice data:', microserviceData)
  
  // Handle both old format (with totals/extras) and new format (flat structure)
  const isOldFormat = microserviceData.totals && microserviceData.extras
  
  let transformed: any
  
  if (isOldFormat) {
    // Old format with nested totals/extras
    const totals = microserviceData.totals || {}
    const extras = microserviceData.extras || {}
    
    transformed = {
      total_quote: {
        status: totals.total_quote?.status || 'not_found',
        value: totals.total_quote?.amount ?? totals.total_quote?.value ?? null,
        currency: totals.total_quote?.currency || 'USD',
        provenance_snippet: totals.total_quote?.provenance_snippet || null,
        notes: totals.total_quote?.notes || ''
      },
      guestroom_total: {
        status: totals.guestroom_total?.status || 'not_found',
        value: totals.guestroom_total?.amount ?? totals.guestroom_total?.value ?? null,
        currency: totals.guestroom_total?.currency || 'USD',
        provenance_snippet: totals.guestroom_total?.provenance_snippet || null,
        notes: totals.guestroom_total?.notes || ''
      },
      meeting_room_total: {
        status: totals.meeting_room_total?.status || 'not_found',
        value: totals.meeting_room_total?.amount ?? totals.meeting_room_total?.value ?? null,
        currency: totals.meeting_room_total?.currency || 'USD',
        provenance_snippet: totals.meeting_room_total?.provenance_snippet || null,
        notes: totals.meeting_room_total?.notes || ''
      },
      fnb_total: {
        status: totals.fnb_total?.status || 'not_found',
        value: totals.fnb_total?.amount ?? totals.fnb_total?.value ?? null,
        currency: totals.fnb_total?.currency || 'USD',
        provenance_snippet: totals.fnb_total?.provenance_snippet || null,
        notes: totals.fnb_total?.notes || ''
      },
      extras: {
        room_nights: extras.room_nights || null,
        nightly_rate: extras.nightly_rate || null,
        tax_rate_pct: extras.tax_rate_pct || null,
        service_rate_pct: extras.service_rate_pct || null,
        fnb_minimum: extras.fnb_minimum || null,
        proposal_url: extras.proposal_url || null,
        guestroom_base: extras.guestroom_base || null,
        guestroom_taxes_fees: extras.guestroom_taxes_fees || null,
        estimated_fnb_gross: extras.estimated_fnb_gross || null,
        effective_value_offsets: extras.effective_value_offsets || []
      }
    }
  } else {
    // New format with flat structure (from Firecrawl)
    transformed = {
      total_quote: {
        status: microserviceData.total_quote?.status || 'not_found',
        value: microserviceData.total_quote?.amount ?? microserviceData.total_quote?.value ?? null,
        currency: microserviceData.total_quote?.currency || 'USD',
        provenance_snippet: microserviceData.total_quote?.provenance_snippet || null,
        notes: microserviceData.total_quote?.notes || ''
      },
      guestroom_total: {
        status: microserviceData.guestroom_total?.status || 'not_found',
        value: microserviceData.guestroom_total?.amount ?? microserviceData.guestroom_total?.value ?? null,
        currency: microserviceData.guestroom_total?.currency || 'USD',
        provenance_snippet: microserviceData.guestroom_total?.provenance_snippet || null,
        notes: microserviceData.guestroom_total?.notes || ''
      },
      meeting_room_total: {
        status: microserviceData.meeting_room_total?.status || 'not_found',
        value: microserviceData.meeting_room_total?.amount ?? microserviceData.meeting_room_total?.value ?? null,
        currency: microserviceData.meeting_room_total?.currency || 'USD',
        provenance_snippet: microserviceData.meeting_room_total?.provenance_snippet || null,
        notes: microserviceData.meeting_room_total?.notes || ''
      },
      fnb_total: {
        status: microserviceData.fnb_total?.status || 'not_found',
        value: microserviceData.fnb_total?.amount ?? microserviceData.fnb_total?.value ?? null,
        currency: microserviceData.fnb_total?.currency || 'USD',
        provenance_snippet: microserviceData.fnb_total?.provenance_snippet || null,
        notes: microserviceData.fnb_total?.notes || ''
      },
      extras: {
        room_nights: microserviceData.room_nights || null,
        nightly_rate: microserviceData.nightly_rate || null,
        tax_rate_pct: microserviceData.tax_rate_pct || null,
        service_rate_pct: microserviceData.service_rate_pct || null,
        fnb_minimum: microserviceData.fnb_minimum || null,
        proposal_url: microserviceData.proposal_url || null,
        guestroom_base: microserviceData.guestroom_base || null,
        guestroom_taxes_fees: microserviceData.guestroom_taxes_fees || null,
        estimated_fnb_gross: microserviceData.estimated_fnb_gross || null,
        effective_value_offsets: microserviceData.effective_value_offsets || []
      }
    }
  }
  
  // Add common fields
  transformed.property = microserviceData.property || {}
  transformed.program = microserviceData.program || {}
  transformed.concessions = microserviceData.concessions || []
  transformed.policies = microserviceData.policies || {}
  transformed.sources = microserviceData.sources || []
  
  console.log('Transformation completed')
  return transformed
}
