# AI Air Ticket Search Agent

AI-powered flight search agent that scrapes `tour.ne.jp` for flight prices, generates Chinese visual reports via Google Gemini, and sends reports via Telegram bot. Supports both one-way and round-trip flights. The project runs as a containerized Python application using headless Chrome for web scraping.

## Features

- **Automated Search**: Scrapes flight data from `tour.ne.jp` for multiple destinations and dates
- **One-Way & Round-Trip**: Supports `AIR_TYPE="0"` (one-way) and `AIR_TYPE="1"` (round-trip with return dates)
- **AI Analysis**: Uses Google Gemini to analyze flight options and generate comprehensive Chinese reports with **individual flight comments** (markdown formatted)
- **Visual Reports**: Generates beautiful HTML reports optimized for mobile (780x1688px, 2x resolution)
- **JPG Output**: Saves reports as JPG, sent as Telegram document (no compression)
- **Chinese Font Support**: Includes Noto CJK, WenQuanYi Micro Hei, and emoji fonts for proper rendering
- **High Contrast**: Updated color scheme with better readability
- **Telegram Integration**: Sends reports as downloadable documents via Telegram bot (preserves quality)
- **Dockerized**: Runs in a Docker container with headless Chrome
- **Dev Mode**: Live code editing via volume mounts (no rebuild needed)

## Tech Stack

- **Language**: Python 3.12
- **Package Manager**: uv (fast Python package manager)
- **AI Model**: Google Gemini (gemini-flash-latest-non-thinking)
- **Web Scraping**: Selenium (headless Chrome)
- **Image Rendering**: Chrome headless screenshot → JPG conversion via Pillow
- **Messaging**: Telegram Bot API
- **Markdown**: markdown library for rendering flight comments
- **Fonts**: Noto CJK, WenQuanYi Micro Hei, Noto Color Emoji
- **Containerization**: Docker + Docker Compose

## Architecture

1. **Config Loader**: Loads search parameters from `.env` file
2. **Scraper**: Headless Chrome scrapes flight data from tour.ne.jp (one-way or round-trip)
3. **HTML Parser**: Converts raw HTML to structured JSON
4. **Report Generator**: AI analyzes flights and generates:
   - Summary note
   - Individual flight comments (markdown) with transfer info, pros/cons, warnings
   - For round-trip: separate outbound and return flight comments
5. **Image Renderer**: Converts HTML report to JPG with automatic resizing for Telegram limits
6. **Telegram Sender**: Sends JPG as document via Telegram bot (no compression, preserves quality)

## Visual Report Features

- **Modern Design**: Beautiful gradient backgrounds with high contrast
- **High Resolution**: Dynamic height, up to 9000px (auto-resized for Telegram)
- **Mobile Optimized**: Vertical phone display format
- **Flight Cards**:
  - One-way: Single card per flight with gradient colors
  - Round-trip: Two linked cards (outbound + return) with stay duration connector
- **AI Comments**: Markdown-formatted analysis for each flight including:
  - Transfer information (self-transfer vs protected)
  - What to watch out for (layover time, visa requirements)
  - Pros and cons
- **Complete Information**: Price, airline, duration, transfers, baggage info
- **Chinese Support**: Proper font rendering for Chinese characters and emojis

## Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)

## Installation

1. **Clone repository:**
   ```sh
   git clone <repository-url>
   cd ai_airticket
   ```

2. **Configure environment:**
   Create `.env` file from sample:
   ```sh
   cp .env.sample .env
   ```
   Edit `.env` with your values. **Telegram Bot Token and Gemini API Key are required.**

   ```dotenv
   # Gemini API Configuration
   GEMINI_API_ENDPOINT="https://your-gemini-endpoint"
   GEMINI_API_KEY="your-gemini-api-key"

   # Flight Search Configuration
   ORIGIN="TYO"
   DESTINATIONS="SIN"
   DEPARTURE_DATES="20260101,20260102"
   AIR_TYPE="0"              # 0 = one-way, 1 = round-trip
   RETURN_DATES="20260110"   # Required when AIR_TYPE="1"

   # Cache Configuration
   USE_CACHE="false"

   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
   TELEGRAM_CHAT_ID="-1003385084352"  # Use negative ID for groups/supergroups
   ```

## Running

### Production Mode
```sh
docker compose up --build
```

### Development Mode (Live Code Editing)
```sh
./run_dev.sh
```

The dev compose file (`docker-compose.dev.yml`) mounts source files as volumes, so changes to Python/HTML files are reflected immediately without rebuilding.

### Available Scripts

- `./run_dev.sh` - Run in development mode with volume mounts
- `./dev.sh` - Local development with virtual environment
- `./run.sh` - Production run via Docker

## Project Structure

```
ai_airticket/
├── .env                      # Environment variables (required)
├── docker-compose.yml        # Production Docker Compose
├── docker-compose.dev.yml    # Dev Docker Compose with volume mounts
├── Dockerfile                # Multi-stage Dockerfile
├── requirements.txt          # Python dependencies
├── run_dev.sh                # Dev mode runner
├── run.sh                    # Production runner
├── dev.sh                    # Local dev runner
├── entrypoint.sh             # Container entry point
├── scraper.py                # Main scraper & orchestration
├── parser.py                 # HTML parser
├── telegram_bot.py           # Telegram bot integration
├── template.html             # HTML report template (mobile optimized)
├── iata-icao.csv            # Airport code database
└── data/                    # Persistent data (Docker volume)
    ├── *.md                 # Cached flight data
    ├── *.jpg                # Generated reports
    └── price_history.db     # SQLite price history
```

## Configuration Rules

- **CRITICAL**: All configuration MUST come from `.env` file loaded via `python-dotenv`
- **NEVER use `os.getenv()` directly** - always call `load_config()` from `scraper.py`
- Required secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GEMINI_API_KEY`, `GEMINI_API_ENDPOINT`
- Search parameters: `ORIGIN`, `DESTINATIONS` (comma-separated), `DEPARTURE_DATES` (comma-separated), `AIR_TYPE`
- Round-trip: Set `AIR_TYPE="1"` and provide `RETURN_DATES` (single date, not comma-separated)

## Output Format

- **Format**: JPG (75% quality)
- **Delivery**: Telegram document (no compression, full quality preserved)
- **Resolution**: Dynamic height (auto-resized if > 9000px tall or > 3000px wide)
- **Fonts**: Noto Sans CJK SC, WenQuanYi Micro Hei, Noto Color Emoji
- **Language**: Chinese (Simplified)
- **Content**: Top 3 cheapest flights with AI-generated comments

## One-Way vs Round-Trip

| Feature | One-Way (`AIR_TYPE="0"`) | Round-Trip (`AIR_TYPE="1"`) |
|---------|--------------------------|----------------------------|
| Required Config | `DEPARTURE_DATES` | `DEPARTURE_DATES` + `RETURN_DATES` |
| Display | Single flight card | Two linked cards (outbound + return) |
| AI Comments | One comment per flight | Separate comments for outbound & return |
| Stay Info | Not shown | Stay duration displayed between cards |

## Recent Updates

- **Round-Trip Support**: Added `AIR_TYPE="1"` with `RETURN_DATES` configuration
- **Two Linked Cards**: Round-trip flights display as connected outbound + return cards
- **Telegram Document**: Reports sent as downloadable files (no compression, preserves quality)
- **Auto-Resize**: Images automatically resized for Telegram limits (9000px height, 3000px width)
- **JPG Output**: Changed from PNG to JPG with 75% quality (smaller file size)
- **AI Flight Comments**: Individual markdown-formatted analysis for each flight
- **Round-Trip AI Comments**: Separate outbound and return flight analysis
- **Chinese Fonts**: Added Noto CJK, WenQuanYi Micro Hei, emoji fonts
- **High Contrast**: Updated color scheme for better readability
- **Dev Mode**: Live code editing without rebuilding
- **Markdown Support**: Flight comments rendered from markdown
- **Fixed CSS Escaping**: Template CSS properly escaped for Python `.format()`

## Important Notes

1. **Virtual environment**: Use `uv venv` to create venv, `uv pip install` for packages
2. **No os.getenv()**: Use `load_config()` function only
3. **Data persistence**: `data/` folder is Docker volume-mounted
4. **Chinese output**: All reports are generated in Chinese
5. **Template escaping**: CSS in template.html uses `{{` and `}}` for Python `.format()`
6. **Telegram Chat ID**: Groups that upgrade to supergroups get new chat IDs (e.g., `-1234567890` → `-1001234567890`). Use `@GetIDsBot` to find the correct ID
7. **Telegram Bot**: Must be added to the group and given permission to send messages/documents

## License

This project is licensed under the terms of the LICENSE file.
