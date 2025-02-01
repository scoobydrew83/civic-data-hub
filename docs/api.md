# Civic Data Hub API Documentation

## Overview

The Civic Data Hub API provides access to comprehensive civic data, including elected officials, district boundaries, and office locations. This RESTful API supports both single-address and bulk queries, with responses in JSON format.

## Base URL

```
https://api.civicdata.hub/v1
```

## Authentication

API requests require an API key passed in the header:

```
Authorization: Bearer your_api_key_here
```

## Endpoints

### 1. Representative Lookup

#### GET /api/v1/lookup

Look up representatives for a given address.

**Parameters:**
- `address` (required): Street address string

**Example Request:**
```bash
curl -X GET "https://api.civicdata.hub/v1/lookup?address=123+Main+St+Springfield+IL" \
     -H "Authorization: Bearer your_api_key_here"
```

**Example Response:**
```json
{
    "address": "123 Main St Springfield IL",
    "normalized_address": "123 main st springfield il",
    "districts": [
        {
            "id": 1,
            "name": "Illinois 7th Congressional District",
            "district_type": "federal_congressional",
            "state_fips": "17",
            "district_code": "CD-7"
        }
    ],
    "officials": [
        {
            "id": 123,
            "full_name": "John Doe",
            "office_title": "U.S. Representative",
            "party": "Independent",
            "email": "john.doe@house.gov",
            "phone": "202-555-0123",
            "website": "https://doe.house.gov"
        }
    ]
}
```

### 2. District Boundaries

#### GET /api/v1/districts

Get district boundaries for a specific location.

**Parameters:**
- `lat` (required): Latitude
- `lng` (required): Longitude

**Example Request:**
```bash
curl -X GET "https://api.civicdata.hub/v1/districts?lat=39.78373&lng=-89.65063" \
     -H "Authorization: Bearer your_api_key_here"
```

**Example Response:**
```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "id": 1,
                "name": "Illinois 7th Congressional District",
                "district_type": "federal_congressional",
                "state_fips": "17",
                "district_code": "CD-7"
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [...]
            }
        }
    ]
}
```

### 3. Bulk Representative Lookup

#### GET /api/v1/bulk-lookup

Look up representatives for multiple addresses in a single request.

**Parameters:**
- `addresses` (required): Array of address strings (max 100)

**Example Request:**
```bash
curl -X GET "https://api.civicdata.hub/v1/bulk-lookup?addresses=123+Main+St+NY&addresses=456+Elm+St+NY" \
     -H "Authorization: Bearer your_api_key_here"
```

**Example Response:**
```json
{
    "results": [
        {
            "address": "123 Main St NY",
            "result": {
                "districts": [...],
                "officials": [...]
            },
            "error": null
        },
        {
            "address": "456 Elm St NY",
            "result": {
                "districts": [...],
                "officials": [...]
            },
            "error": null
        }
    ]
}
```

### 4. Official Details

#### GET /api/v1/official/{official_id}

Get detailed information about a specific elected official.

**Parameters:**
- `official_id` (required): ID of the official

**Example Request:**
```bash
curl -X GET "https://api.civicdata.hub/v1/official/123" \
     -H "Authorization: Bearer your_api_key_here"
```

**Example Response:**
```json
{
    "official": {
        "id": 123,
        "full_name": "John Doe",
        "office_title": "U.S. Representative",
        "party": "Independent",
        "email": "john.doe@house.gov",
        "phone": "202-555-0123",
        "website": "https://doe.house.gov",
        "district_name": "Illinois 7th Congressional District",
        "district_type": "federal_congressional",
        "state_fips": "17",
        "district_code": "CD-7"
    },
    "offices": [
        {
            "office_type": "district",
            "address_line1": "123 Capitol Street",
            "address_line2": "Suite 100",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701",
            "phone": "217-555-0123",
            "location": {
                "type": "Point",
                "coordinates": [-89.65063, 39.78373]
            }
        }
    ]
}
```

### 5. District Search

#### GET /api/v1/districts/search

Search for districts by name or type.

**Parameters:**
- `query` (required): Search string
- `type` (optional): District type filter
- `state` (optional): State FIPS code filter

**Example Request:**
```bash
curl -X GET "https://api.civicdata.hub/v1/districts/search?query=7th+congressional&state=17" \
     -H "Authorization: Bearer your_api_key_here"
```

**Example Response:**
```json
{
    "results": [
        {
            "id": 1,
            "name": "Illinois 7th Congressional District",
            "district_type": "federal_congressional",
            "state_fips": "17",
            "district_code": "CD-7",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [...]
            }
        }
    ]
}
```

## Error Handling

The API uses standard HTTP response codes:

- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 408: Request Timeout
- 429: Too Many Requests
- 500: Internal Server Error

Error responses include a detail message:

```json
{
    "detail": "Error message describing the problem"
}
```

## Rate Limiting

- Free tier: 1,000 requests per day
- Standard tier: 10,000 requests per day
- Enterprise tier: Custom limits

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1612223399
```

## Data Updates

- Representative data is updated daily
- District boundaries are updated upon redistricting
- Office locations are updated weekly

## Support

For API support, contact:
- Email: api@civicdata.hub
- Documentation: https://docs.civicdata.hub
- Status: https://status.civicdata.hub