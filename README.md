# Hotel Quote Parser

A professional AI-powered system for extracting structured hotel quote data from emails, PDFs, and web proposals. Built with Next.js frontend and FastAPI microservice architecture.

## Features

- **Dual Input Processing**: Handle email content + proposal files/URLs simultaneously
- **AI-Powered Extraction**: Uses OpenAI GPT-4 for intelligent data parsing
- **Multi-Format Support**: PDF, HTML, and plain text files
- **Smart Data Merging**: Proposal data takes precedence over email data
- **Comprehensive Output**: Extracts totals, breakdowns, concessions, and policies
- **Modern UI**: Clean, responsive interface with real-time feedback
- **Export Options**: JSON and CSV download capabilities

## Prerequisites

- **Node.js 18+** and npm
- **Python 3.11+** and pip
- **OpenAI API key** (required for AI extraction)

## Quick Start

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd hotel-quote-parser

# Install frontend dependencies
npm install

# Install Python dependencies
cd microservice
pip install -r requirements.txt
cd ..
```

### 2. Environment Setup

Create a `.env.local` file in the root directory:

```bash
# Required: OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Override default model
OPENAI_MODEL=gpt-4o-mini

# Optional: Microservice URL (defaults to localhost:8000)
MICROSERVICE_URL=http://localhost:8000

# Optional: Supabase Database Configuration
# Get these from your Supabase project settings
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Optional: Firecrawl API key for web scraping
# FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

**Required API Keys:**
- **OpenAI API key**: https://platform.openai.com/api-keys
- **Supabase** (optional but recommended): https://supabase.com/docs/guides/getting-started/tutorials/create-new-project

### Database Setup (Optional)

The application can store extracted data in a Supabase PostgreSQL database for persistence and analysis:

1. **Create a Supabase project**: https://supabase.com
2. **Get your credentials** from Project Settings → API
3. **Add to .env.local**:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

**Note**: The application works without Supabase, but data won't be persisted between sessions.

#### Database Schema (Supabase)

If using Supabase, the application creates these tables automatically:

- **hotel_quote_requests**: Request metadata and processing info
- **hotel_quote_data**: Extracted financial data and totals  
- **hotel_properties**: Property information and contacts
- **hotel_concessions**: Special offers and concessions
- **hotel_policies**: Hotel policies and terms

**Setup**: Run `script/setup_database.sql` in your Supabase SQL Editor to create the tables manually.

### 3. Start the Application

#### Option A: Use the startup script (Recommended)
```bash
chmod +x start.sh
./start.sh
```

#### Option B: Manual startup
```bash
# Terminal 1: Start microservice
cd microservice
python main.py

# Terminal 2: Start frontend
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Microservice API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## Project Structure

```
hotel-quote-parser/
├── app/                          # Next.js frontend
│   ├── page.tsx                 # Main UI component
│   ├── api/process/route.ts     # API route handler
│   ├── layout.tsx               # App layout
│   └── globals.css              # Global styles
├── microservice/                # FastAPI backend
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database operations
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Container configuration
├── script/                     # Core extraction logic
│   ├── extract_hotel_quotes.py # AI extraction script
│   └── hotel_quote_prompt.txt  # OpenAI prompt template
├── lib/                        # Utility functions
├── start.sh                    # Startup script
├── test_microservice.py        # API testing
└── README.md                   # This file
```

## API Endpoints

### POST `/extract`
Main extraction endpoint for processing files and content.

**Form Data:**
- `email_content` (optional): Text content from email
- `email_file` (optional): Email file upload (PDF/HTML)
- `proposal_file` (optional): Proposal file upload (PDF/HTML)
- `proposal_url` (optional): Direct URL to proposal

**Response:**
```json
{
  "success": true,
  "data": {
    "total_quote": {
      "status": "derived",
      "value": 72975.6,
      "currency": "USD",
      "provenance_snippet": "..."
    },
    "guestroom_total": { ... },
    "meeting_room_total": { ... },
    "fnb_total": { ... },
    "extras": {
      "room_nights": 240,
      "nightly_rate": 192,
      "service_rate_pct": 24,
      "tax_rate_pct": 8.45
    },
    "concessions": ["Waived meeting room rental with F&B minimum"],
    "sources": ["proposal", "email"]
  }
}
```

### GET `/health`
Health check endpoint.

## Testing

Test the microservice API:

```bash
python test_microservice.py
```

## Docker Deployment

### Build and run with Docker Compose

```bash
# Build images
docker build -t hotel-quote-frontend .
docker build -t hotel-quote-microservice ./microservice

# Run with docker-compose (create docker-compose.yml)
docker-compose up
```

### Microservice only
```bash
cd microservice
docker build -t hotel-quote-microservice .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key hotel-quote-microservice
```

## Data Extraction Details

The system extracts the following structured data:

### Core Financials
- **Total Quote**: Overall event cost
- **Guestroom Total**: Accommodation costs with taxes/fees
- **Meeting Room Total**: Venue rental costs
- **F&B Total**: Food and beverage with service charges

### Status Types
- **Explicit**: Directly stated in the proposal
- **Derived**: Calculated from available data
- **Conditional**: Subject to conditions (e.g., F&B minimum)
- **Not Found**: Information not available

### Additional Data
- **Concessions**: Special offers and conditions
- **Property Details**: Hotel information
- **Event Program**: Schedule and agenda
- **Policies**: Cancellation, attrition, etc.

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Ensure `OPENAI_API_KEY` is set in `.env.local`
   - Verify the key is valid and has sufficient credits

2. **Microservice Won't Start**
   - Check Python version (3.11+ required)
   - Verify all dependencies are installed: `pip install -r microservice/requirements.txt`

3. **Frontend Won't Start**
   - Check Node.js version (18+ required)
   - Clear cache: `rm -rf .next && npm install`

4. **File Upload Issues**
   - Supported formats: PDF, HTML, TXT
   - Maximum file size: 10MB

5. **Database Connection Issues**
   - Verify Supabase credentials in `.env.local`
   - Check if Supabase project is active
   - Ensure database tables exist (created automatically on first use)

### Logs
- Frontend logs: Check terminal running `npm run dev`
- Microservice logs: Check terminal running `python main.py`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Open an issue on GitHub with detailed information

---

**Note**: This application requires an OpenAI API key for AI-powered extraction. Ensure you have sufficient API credits for your usage.
