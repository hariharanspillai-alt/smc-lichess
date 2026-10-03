# SMC Lichess Tournament Creator

A CLI tool for automatically creating SMC Chess Club weekly Swiss tournaments on Lichess.

## Overview

This tool creates scheduled Swiss tournaments for the SMC Academy Chess Club on Lichess. It automatically determines the next sequence number and creates four tournaments per week:

- Saturday tournaments (12:00 PM Pacific Time)
  - `<N> SMC Saturday Above 1000`
  - `<N> SMC Saturday Below 1000`
- Sunday tournaments (12:00 PM Pacific Time)
  - `<N> SMC Sunday Above 1000`
  - `<N> SMC Sunday Below 1000`

## Prerequisites

1. **Lichess Account**: You need a Lichess account with `tournament:write` scope
2. **SMC Academy Team**: You need access to the SMC Academy Lichess team
3. **Personal Access Token**: Create one at https://lichess.org/account/oauth/token

### Required OAuth Scopes

- `tournament:write` - Create tournaments
- `team:read` - Read team information

## Installation

### Option 1: Using pip

```bash
pip install -r requirements.txt
```

### Option 2: Using npm (for convenience scripts)

```bash
npm install
```

## Configuration

### Setup Environment Variables

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:

```env
LICHESS_API_TOKEN=your_personal_access_token_here
LICHESS_TEAM_ID=your_smc_academy_team_id
```

### Finding Your Team ID

1. Visit your SMC Academy team page on Lichess
2. The team ID is in the URL: `https://lichess.org/team/YOUR_TEAM_ID`
3. Copy the ID (it's usually a short alphanumeric string)

## API Reference

### Swiss Tournament Creation Endpoint

**Endpoint**: `POST /api/swiss/new/{teamId}`

**Content-Type**: `application/x-www-form-urlencoded`

**Authentication**: `Authorization: Bearer <token>`

**Required Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `clock.limit` | integer | Initial clock time in seconds (900 = 15 minutes) |
| `clock.increment` | integer | Clock increment in seconds (30) |
| `nbRounds` | integer | Number of rounds (5) |
| `name` | string | Tournament name |
| `startsAt` | integer | Start timestamp in milliseconds (UTC) |

**Optional Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `rated` | boolean | Whether games are rated (true) |
| `variant` | string | Chess variant (standard) |
| `description` | string | Tournament description |
| `conditions.minRating.rating` | integer | Minimum rating (1000 for "Above 1000") |
| `conditions.maxRating.rating` | integer | Maximum rating (999 for "Below 1000") |

### List Team Swiss Tournaments

**Endpoint**: `GET /api/team/{teamId}/swiss?max=100`

**Response**: NDJSON stream of Swiss tournament objects

### Test Token

**Endpoint**: `GET /api/token/test`

**Purpose**: Verify token validity and get granted scopes

## Usage

### Show Help

```bash
python -m src.cli --help
```

### Create Tournaments

#### Create for Saturday Only

```bash
npm run create --day saturday
# or
python -m src.cli create --day saturday
```

#### Create for Sunday Only

```bash
npm run create --day sunday
# or
python -m src.cli create --day sunday
```

#### Create All Four Tournaments for the Week

```bash
npm run create:week
# or
python -m src.cli week
```

#### Dry Run (Show What Would Be Created)

```bash
python -m src.cli week --dry-run
python -m src.cli create --day saturday --dry-run
```

### Other Commands

```bash
# Check status and configuration
python -m src.cli status

# Show next sequence number
python -m src.cli sequence
```

## Tournament Configuration

All tournaments have the following configuration:

| Setting | Value |
|---------|-------|
| Format | Lichess Swiss |
| Rounds | 5 |
| Rated | Yes |
| Time Control | 15+30 (15 minutes, 30 seconds increment) |
| Variant | Standard Chess |
| Start Time | 12:00 PM Pacific Time (America/Los_Angeles) |

## Rating Restrictions

### Above 1000 Category

Uses Lichess API native rating restriction:
- `conditions.minRating.rating = 1000`
- Minimum Lichess rating: 1000 or higher

### Below 1000 Category

Uses Lichess API native rating restriction:
- `conditions.maxRating.rating = 999`
- Maximum Lichess rating: below 1000

**Note**: Lichess uses best rating from the last 7 days for min rating, and best rating from the last 7 days for max rating (based on [Lichess API docs](https://lichess.org/api)).

## Access Control

Tournaments are restricted to the SMC Academy team using the `teamId` path parameter in the creation endpoint. Only team members can participate.

## Duplicate Prevention

The tool implements several layers of duplicate protection:

1. **Sequence Number Check**: Before creating, it queries existing tournaments and determines the next sequence number
2. **Name Check**: Checks if a tournament with the exact name already exists
3. **Idempotent**: Running the command multiple times will not create duplicates

Example output when running twice:
```
Already exists — 346 SMC Saturday Above 1000
Already exists — 346 SMC Saturday Below 1000
No duplicates created.
```

## Sequence Number Determination

The sequence number is determined from existing SMC tournaments:

1. Query all Swiss tournaments for the team: `GET /api/team/{teamId}/swiss`
2. Parse tournament names matching pattern: `^(\d+)\s+SMC\s+(Saturday|Sunday)\s+(Above 1000|Below 1000)$`
3. Find the highest sequence number
4. Next sequence = highest + 1

This ensures:
- No gaps in sequence numbers
- Saturday and Sunday in the same week share the same sequence
- Sequence continues from where it left off

## Timezone Handling

Start times are specified in **America/Los_Angeles** timezone, which correctly handles:
- Standard Time (PST, UTC-8)
- Daylight Saving Time (PDT, UTC-7)

The start time is converted to UTC milliseconds before sending to the Lichess API.

## Error Handling

The tool handles various error conditions:

| Error | Message |
|-------|---------|
| Missing token | `ERROR: LICHESS_API_TOKEN is not configured.` |
| Missing team ID | `ERROR: LICHESS_TEAM_ID is not configured.` |
| Invalid token | `ERROR: Lichess authentication failed. Check LICHESS_API_TOKEN.` |
| No permission | `ERROR: Authenticated Lichess account does not have permission to create Swiss tournaments for this team.` |
| API rate limit | Automatically retries with exponential backoff |
| Network failure | Retries up to 3 times before failing |

## Examples

### Dry Run Example

```bash
$ python -m src.cli week --dry-run

============================================================
SMC Lichess Tournament Creator
Version: 1.0.0
============================================================

DRY RUN - No tournaments will be created

Sequence: 346

Saturday:
  346 SMC Saturday Above 1000
    Start: 2026-08-16 12:00 PDT
    Timezone: Pacific Time (America/Los_Angeles)
    Rounds: 5
    Clock: 15+30
    Rated: yes
    Variant: standard
    Team: your_team_id
    Min Rating: 1000

  346 SMC Saturday Below 1000
    Start: 2026-08-16 12:00 PDT
    Timezone: Pacific Time (America/Los_Angeles)
    Rounds: 5
    Clock: 15+30
    Rated: yes
    Variant: standard
    Team: your_team_id
    Max Rating: 999

...
```

### Creation Example

```bash
$ python -m src.cli week

============================================================
SMC Lichess Tournament Creator
Version: 1.0.0
============================================================

Creating tournaments for upcoming Saturday and Sunday...

SUCCESS

346 SMC Saturday Above 1000
https://lichess.org/swiss/abcd1234

346 SMC Saturday Below 1000
https://lichess.org/swiss/efgh5678

346 SMC Sunday Above 1000
https://lichess.org/swiss/ijkl9012

346 SMC Sunday Below 1000
https://lichess.org/swiss/mnop3456

Created: 4
Skipped: 0
Failed: 0
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v
```

### Test Coverage

- Sequence number determination
- Duplicate tournament detection
- Day scheduling (Saturday/Sunday at 12:00 PM Pacific)
- Timezone handling (DST transitions)
- Tournament configuration validation
- API error handling (401, 403, 404, 429, 500)

## Rate Limiting

The tool respects Lichess API rate limits:
- Authenticated requests: 30 items/second
- Automatic retry with exponential backoff for 429 errors
- Sequential requests (no parallel hammering)

## Project Structure

```
smc-lichess/
├── src/
│   ├── cli.py              # CLI entry point and commands
│   ├── lichess_api.py      # Lichess API client
│   ├── swiss_creator.py    # Tournament creation logic
│   ├── sequence.py         # Sequence number determination
│   ├── schedule.py         # Tournament scheduling
│   ├── validation.py       # Configuration validation
│   └── config.py           # Configuration management
├── tests/
│   ├── test_sequence.py    # Sequence number tests
│   ├── test_schedule.py    # Schedule tests
│   ├── test_creator.py     # Tournament creator tests
│   └── test_validation.py  # Validation tests
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore file
├── package.json            # npm package config
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## License

MIT

## Sources

- [Lichess API Documentation](https://lichess.org/api)
- [Lichess Swiss Tournament Creation](https://lichess.org/api#operation/createSwiss)