-- Civic Data Hub Database Schema

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Districts table
CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    district_type VARCHAR(50) NOT NULL,  -- federal_congressional, state_senate, etc.
    state_fips VARCHAR(2),
    district_code VARCHAR(50),
    name VARCHAR(100),
    boundary GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Officials table
CREATE TABLE officials (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    office_title VARCHAR(100) NOT NULL,
    district_id INTEGER REFERENCES districts(id),
    party VARCHAR(50),
    email VARCHAR(255),
    phone VARCHAR(20),
    website VARCHAR(255),
    term_start DATE,
    term_end DATE,
    source_type VARCHAR(50),  -- openstates, dnc_roster, etc.
    source_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Offices table (physical locations)
CREATE TABLE offices (
    id SERIAL PRIMARY KEY,
    official_id INTEGER REFERENCES officials(id),
    office_type VARCHAR(50),  -- main, district, etc.
    address_line1 VARCHAR(100),
    address_line2 VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(2),
    zip VARCHAR(10),
    location GEOMETRY(Point, 4326),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data sources tracking
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    last_sync TIMESTAMP,
    status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Address cache table for faster lookups
CREATE TABLE address_cache (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    normalized_address TEXT,
    location GEOMETRY(Point, 4326),
    last_lookup TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(normalized_address)
);

-- Spatial indices
CREATE INDEX districts_boundary_idx ON districts USING GIST (boundary);
CREATE INDEX offices_location_idx ON offices USING GIST (location);
CREATE INDEX address_cache_location_idx ON address_cache USING GIST (location);

-- Update triggers for timestamp management
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_districts_updated_at
    BEFORE UPDATE ON districts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_officials_updated_at
    BEFORE UPDATE ON officials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_offices_updated_at
    BEFORE UPDATE ON offices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();