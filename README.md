# Civic Data Hub

An open-source civic data aggregation and lookup service that combines multiple public data sources to provide comprehensive information about elected officials, districts, and civic engagement opportunities.

## Features

- Address-based representative lookup
- District boundary information
- Multi-level government coverage (Federal, State, Local)
- Bulk data import/export capabilities
- RESTful API
- Geographic data visualization

## Data Sources

- OpenStates API
- Census TIGER/Line Shapefiles
- DNC Elected Officials Roster
- Open Civic Data
- Local government data feeds

## Getting Started

### Prerequisites

- PostgreSQL 13+ with PostGIS extension
- Node.js 16+
- Python 3.8+

### Installation

1. Clone the repository
```bash
git clone https://github.com/scoobydrew83/civic-data-hub.git
cd civic-data-hub
```

2. Install dependencies
```bash
npm install
python -m pip install -r requirements.txt
```

3. Set up the database
```bash
psql -f db/init.sql
```

4. Run initial data sync
```bash
python scripts/sync_data.py
```

## API Usage

### Lookup Representatives by Address
```bash
GET /api/v1/lookup?address=123+Main+St+Springfield+IL
```

### Get District Boundaries
```bash
GET /api/v1/districts?lat=39.78373&lng=-89.65063
```

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.