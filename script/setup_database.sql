-- Hotel Quote Parser Database Schema
-- Run this in your Supabase SQL Editor to create the required tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Hotel Quote Requests Table
CREATE TABLE IF NOT EXISTS hotel_quote_requests (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    email_content TEXT,
    email_file_name VARCHAR(255),
    email_file_size INTEGER,
    proposal_file_name VARCHAR(255),
    proposal_file_size INTEGER,
    proposal_url TEXT,
    urls_found TEXT[],
    sources_used TEXT[],
    content_length INTEGER,
    firecrawl_scraped BOOLEAN DEFAULT FALSE,
    firecrawl_content_length INTEGER,
    processing_status VARCHAR(50) DEFAULT 'pending'
);

-- Hotel Quote Data Table
CREATE TABLE IF NOT EXISTS hotel_quote_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    request_id UUID REFERENCES hotel_quote_requests(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Total Quote
    total_quote_status VARCHAR(50),
    total_quote_value DECIMAL(15,2),
    total_quote_currency VARCHAR(10) DEFAULT 'USD',
    total_quote_provenance TEXT,
    total_quote_notes TEXT,
    
    -- Guestroom Total
    guestroom_total_status VARCHAR(50),
    guestroom_total_value DECIMAL(15,2),
    guestroom_total_currency VARCHAR(10) DEFAULT 'USD',
    guestroom_total_provenance TEXT,
    guestroom_total_notes TEXT,
    
    -- Meeting Room Total
    meeting_room_total_status VARCHAR(50),
    meeting_room_total_value DECIMAL(15,2),
    meeting_room_total_currency VARCHAR(10) DEFAULT 'USD',
    meeting_room_total_provenance TEXT,
    meeting_room_total_notes TEXT,
    
    -- F&B Total
    fnb_total_status VARCHAR(50),
    fnb_total_value DECIMAL(15,2),
    fnb_total_currency VARCHAR(10) DEFAULT 'USD',
    fnb_total_provenance TEXT,
    fnb_total_notes TEXT,
    
    -- Extras
    room_nights INTEGER,
    nightly_rate DECIMAL(10,2),
    tax_rate_pct DECIMAL(5,2),
    service_rate_pct DECIMAL(5,2),
    fnb_minimum DECIMAL(15,2),
    proposal_url TEXT,
    guestroom_base DECIMAL(15,2),
    guestroom_taxes_fees DECIMAL(15,2),
    estimated_fnb_gross DECIMAL(15,2),
    effective_value_offsets TEXT[]
);

-- Hotel Properties Table
CREATE TABLE IF NOT EXISTS hotel_properties (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    request_id UUID REFERENCES hotel_quote_requests(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    property_name VARCHAR(255),
    property_address TEXT,
    property_phone VARCHAR(50),
    property_email VARCHAR(255),
    property_website TEXT,
    contact_name VARCHAR(255),
    contact_title VARCHAR(255),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(255)
);

-- Hotel Concessions Table
CREATE TABLE IF NOT EXISTS hotel_concessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    request_id UUID REFERENCES hotel_quote_requests(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    concession_text TEXT NOT NULL,
    concession_type VARCHAR(100),
    monetary_value DECIMAL(15,2),
    currency VARCHAR(10) DEFAULT 'USD'
);

-- Hotel Policies Table
CREATE TABLE IF NOT EXISTS hotel_policies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    request_id UUID REFERENCES hotel_quote_requests(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    policy_type VARCHAR(100),
    policy_text TEXT,
    policy_details JSONB
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_hotel_quote_requests_created_at ON hotel_quote_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_hotel_quote_data_request_id ON hotel_quote_data(request_id);
CREATE INDEX IF NOT EXISTS idx_hotel_properties_request_id ON hotel_properties(request_id);
CREATE INDEX IF NOT EXISTS idx_hotel_concessions_request_id ON hotel_concessions(request_id);
CREATE INDEX IF NOT EXISTS idx_hotel_policies_request_id ON hotel_policies(request_id);

-- Enable Row Level Security (RLS)
ALTER TABLE hotel_quote_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE hotel_quote_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE hotel_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE hotel_concessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE hotel_policies ENABLE ROW LEVEL SECURITY;

-- Create policies for anonymous access (adjust as needed for your security requirements)
CREATE POLICY "Allow anonymous access to hotel_quote_requests" ON hotel_quote_requests FOR ALL USING (true);
CREATE POLICY "Allow anonymous access to hotel_quote_data" ON hotel_quote_data FOR ALL USING (true);
CREATE POLICY "Allow anonymous access to hotel_properties" ON hotel_properties FOR ALL USING (true);
CREATE POLICY "Allow anonymous access to hotel_concessions" ON hotel_concessions FOR ALL USING (true);
CREATE POLICY "Allow anonymous access to hotel_policies" ON hotel_policies FOR ALL USING (true);
