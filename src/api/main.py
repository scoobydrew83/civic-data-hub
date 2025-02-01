"""FastAPI implementation for Civic Data Hub."""

from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import asyncpg
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import json

app = FastAPI(title="Civic Data Hub API")

# Database connection configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "database": "civic_data_hub"
}

# Models
class Official(BaseModel):
    id: int
    full_name: str
    office_title: str
    party: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    website: Optional[str]

class District(BaseModel):
    id: int
    name: str
    district_type: str
    state_fips: Optional[str]
    district_code: str

class RepresentativeResponse(BaseModel):
    address: str
    normalized_address: str
    districts: List[District]
    officials: List[Official]

@app.on_event("startup")
async def startup():
    """Create database pool on startup."""
    app.state.pool = await asyncpg.create_pool(**DATABASE_CONFIG)
    app.state.geocoder = Nominatim(user_agent="civic_data_hub")

@app.on_event("shutdown")
async def shutdown():
    """Close database pool on shutdown."""
    await app.state.pool.close()

async def geocode_address(address: str) -> tuple:
    """Geocode address to coordinates."""
    try:
        location = app.state.geocoder.geocode(address)
        if location:
            return location.latitude, location.longitude
        raise HTTPException(status_code=404, detail="Address not found")
    except GeocoderTimedOut:
        raise HTTPException(status_code=408, detail="Geocoding service timeout")

@app.get("/api/v1/lookup", response_model=RepresentativeResponse)
async def lookup_representatives(address: str):
    """Look up representatives for a given address."""
    
    # First check the cache
    async with app.state.pool.acquire() as conn:
        cached = await conn.fetchrow('''
            SELECT * FROM address_cache 
            WHERE normalized_address = $1 
            AND expires_at > CURRENT_TIMESTAMP
        ''', address.lower())
        
        if cached:
            location = cached['location']
        else:
            # Geocode the address
            lat, lon = await geocode_address(address)
            location = f'POINT({lon} {lat})'
            
            # Cache the result
            await conn.execute('''
                INSERT INTO address_cache (address, normalized_address, location, expires_at)
                VALUES ($1, $2, ST_GeomFromText($3, 4326), CURRENT_TIMESTAMP + INTERVAL '30 days')
                ON CONFLICT (normalized_address) 
                DO UPDATE SET
                    location = EXCLUDED.location,
                    expires_at = EXCLUDED.expires_at
            ''', address, address.lower(), location)
        
        # Find districts that contain this point
        districts = await conn.fetch('''
            SELECT id, name, district_type, state_fips, district_code
            FROM districts
            WHERE ST_Contains(boundary, ST_GeomFromText($1, 4326))
        ''', location)
        
        if not districts:
            raise HTTPException(status_code=404, detail="No districts found for this address")
        
        # Get officials for these districts
        officials = await conn.fetch('''
            SELECT id, full_name, office_title, party, email, phone, website
            FROM officials
            WHERE district_id = ANY($1)
        ''', [d['id'] for d in districts])
        
        return {
            "address": address,
            "normalized_address": address.lower(),
            "districts": [dict(d) for d in districts],
            "officials": [dict(o) for o in officials]
        }

@app.get("/api/v1/districts")
async def get_district_boundaries(lat: float, lng: float):
    """Get district boundaries for a point."""
    async with app.state.pool.acquire() as conn:
        districts = await conn.fetch('''
            SELECT 
                id, 
                name, 
                district_type, 
                state_fips, 
                district_code,
                ST_AsGeoJSON(boundary) as geometry
            FROM districts
            WHERE ST_Contains(boundary, ST_SetSRID(ST_MakePoint($1, $2), 4326))
        ''', lng, lat)
        
        if not districts:
            raise HTTPException(status_code=404, detail="No districts found for this location")
        
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "id": d['id'],
                        "name": d['name'],
                        "district_type": d['district_type'],
                        "state_fips": d['state_fips'],
                        "district_code": d['district_code']
                    },
                    "geometry": json.loads(d['geometry'])
                }
                for d in districts
            ]
        }

@app.get("/api/v1/bulk-lookup")
async def bulk_lookup_representatives(
    addresses: List[str] = Query(..., max_length=100)
):
    """Bulk lookup of representatives for multiple addresses."""
    results = []
    async with app.state.pool.acquire() as conn:
        for address in addresses:
            try:
                result = await lookup_representatives(address)
                results.append({"address": address, "result": result, "error": None})
            except HTTPException as e:
                results.append({"address": address, "result": None, "error": str(e.detail)})
            except Exception as e:
                results.append({"address": address, "result": None, "error": str(e)})
    
    return {"results": results}

@app.get("/api/v1/official/{official_id}")
async def get_official_details(official_id: int):
    """Get detailed information about an official."""
    async with app.state.pool.acquire() as conn:
        # Get official details
        official = await conn.fetchrow('''
            SELECT 
                o.*,
                d.name as district_name,
                d.district_type,
                d.state_fips,
                d.district_code
            FROM officials o
            JOIN districts d ON o.district_id = d.id
            WHERE o.id = $1
        ''', official_id)
        
        if not official:
            raise HTTPException(status_code=404, detail="Official not found")
        
        # Get office locations
        offices = await conn.fetch('''
            SELECT 
                office_type,
                address_line1,
                address_line2,
                city,
                state,
                zip,
                phone,
                ST_AsGeoJSON(location) as location
            FROM offices
            WHERE official_id = $1
        ''', official_id)
        
        return {
            "official": dict(official),
            "offices": [dict(o) for o in offices]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
