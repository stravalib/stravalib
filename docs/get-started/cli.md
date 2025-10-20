# Use the stravalib CLI

The `stravalib` package now ships with a comprehensive Typer-based command line
interface. It mirrors the full `Client` surface area, making it easy to perform
ad-hoc queries or build shell pipelines without writing Python scripts.

## Installation and setup

Install the package (or your local clone) and make sure the standard Strava
environment variables are exported:

```bash
uv pip install -e .

export STRAVA_CLIENT_ID=12345
export STRAVA_CLIENT_SECRET=...    # keep this secret!
export STRAVA_ACCESS_TOKEN=...
export STRAVA_REFRESH_TOKEN=...
export STRAVA_TOKEN_EXPIRES_AT=1700000000
```

Every command also accepts runtime overrides: `--access-token`,
`--refresh-token`, `--token-expires`, and `--rate-limit/--no-rate-limit`.

List the full command tree:

```bash
uv run stravalib --help
```

The top-level shortcuts (`whoami`, `activities-recent`, `activity`, `activity-streams`)
remain for muscle memory. All other functionality is grouped under
subcommands:

| Group | Highlights |
|-------|------------|
| `auth` | Generate authorization URLs, exchange/refresh tokens, deauthorize |
| `athlete` | Profile, zones, stats, KOMs, club memberships |
| `activities` | List/get, create/update, uploads (with optional polling), comments, zones, photos, laps, streams, kudos |
| `clubs` | Fetch club details, members, activities, admins, join/leave |
| `segments` | Segment lookup, starred segments, effort searches, explore, streams |
| `routes` | Athlete routes and route streams |
| `gear` | Fetch bike/shoe metadata |
| `subscriptions` | Manage webhook subscriptions and validate callbacks |

## Usage examples

### Inspect the current athlete

```bash
uv run stravalib athlete profile
```

### Review recent activities

```bash
uv run stravalib activities list --limit 10 --after 2025-01-01
```

### Upload a FIT file and wait for processing

```bash
uv run stravalib activities upload ./ride.fit --data-type fit --poll
```

### Explore segments in a bounding box

```bash
uv run stravalib segments explore \
    --south-lat 29.60 --west-lng -95.80 \
    --north-lat 29.90 --east-lng -95.10
```

### Manage webhook subscriptions

```bash
uv run stravalib subscriptions create \
    --client-id $STRAVA_CLIENT_ID \
    --client-secret $STRAVA_CLIENT_SECRET \
    --callback-url https://example.com/strava/webhook

uv run stravalib subscriptions list \
    --client-id $STRAVA_CLIENT_ID \
    --client-secret $STRAVA_CLIENT_SECRET
```

### Quick reference

Use `--help` on any subcommand to discover parameter details, for example:

```bash
uv run stravalib segments efforts --help
```

All results are emitted as JSON. Pass `--output-file path.json` to write the
response to disk instead of stdout, and adjust formatting with `--indent`.
