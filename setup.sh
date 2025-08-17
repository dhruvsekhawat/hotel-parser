#!/bin/bash

# Hotel Quote Parser - Setup Script
# This script sets up the development environment

echo "Setting up Hotel Quote Parser..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed."
    echo "   Please install Node.js 18+ from: https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    echo "   Please install Python 3.11+ from: https://python.org/"
    exit 1
fi

echo "Prerequisites check passed"

# Install frontend dependencies
echo "Installing frontend dependencies..."
npm install

# Install Python dependencies
echo "Installing Python dependencies..."
cd microservice
pip install -r requirements.txt
cd ..

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file..."
    cat > .env.local << EOF
# Required: OpenAI API key for AI-powered extraction
# Get your key from: https://platform.openai.com/api-keys
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
EOF
    echo "Please edit .env.local and add your OpenAI API key"
    echo "Note: Supabase configuration is optional but recommended for data persistence"
else
    echo ".env.local already exists"
fi

# Make startup script executable
chmod +x start.sh

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env.local and add your OpenAI API key"
echo "2. Run './start.sh' to start the application"
echo "3. Visit http://localhost:3000"
echo ""
echo "For more information, see README.md"
