# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered air ticket search agent that scrapes `tour.ne.jp` for flight prices, generates Chinese visual reports via Google Gemini, and sends PNG image reports via Telegram bot. The project runs as a containerized Python application using headless Chrome for web scraping.

## Development Commands

### Local Development
```bash
# Set up virtual environment and install dependencies (ALWAYS use uv)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run the scraper locally
./dev.sh  # or: source .venv/bin/activate && python scraper.py

# Run tests
source .venv/bin/activate
python test_chrome_rendering.py
python test_html_report.py
python test_price_history.py
python test_parse.py
```

### Docker Development
```bash
# Build and run with Docker
docker compose up --build

# Build image manually
docker build -t ai_airticket_scraper .

# Run container directly (uses run.sh)
./run.sh
```

## Architecture

### Entry Points
- **`scraper.py`**: Main entry point. Orchestrates scraping, parsing, report generation, and Telegram delivery
- **`dev.sh`**: Local development runner (activates venv, runs scraper.py)
- **`entrypoint.sh`**: Docker container entry point (runs scraper.py inside container)

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| Config Loader | `scraper.py:load_config()` | Loads all settings from `.env` via python-dotenv |
| Web Scraper | `scraper.py:scrape_flights()` | Selenium headless Chrome scraping from tour.ne.jp |
| HTML Parser | `parser.py:parse_flight_data()` | BeautifulSoup + lxml for HTML→JSON conversion |
| Report Generator | `scraper.py:generate_report()` | Calls Gemini API for HTML report generation |
| PNG Renderer | `scraper.py:render_html_to_png()` | Headless Chrome screenshot of HTML report |
| Telegram Sender | `telegram_bot.py` | Sends messages and photos via Telegram Bot API |

### Data Flow
```
.env config → scrape_flights() → parse_flight_data() → generate_report()
                                                               ↓
                                            Gemini API → HTML → PNG → Telegram
```

### Configuration Rules
- **CRITICAL**: All configuration MUST come from `.env` file loaded via `python-dotenv`
- **NEVER use `os.getenv()` directly** - always call `load_config()` from `scraper.py`
- Required secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GEMINI_API_KEY`, `GEMINI_API_ENDPOINT`
- Search parameters: `ORIGIN`, `DESTINATIONS` (comma-separated), `DEPARTURE_DATES` (comma-separated), `AIR_TYPE`

### Web Scraping Notes
- Target: `https://www.tour.ne.jp/w_air/list/`
- Wait strategy: Fixed 55-second sleep (WebDriverWait is disabled - causes crashes in Docker)
- Chrome options required for Docker: `--headless`, `--no-sandbox`, `--disable-dev-shm-usage`
- Output format: JSON saved to `data/{ORIGIN}-{DEST}-{DATE}-{timestamp}.md`

### Report Generation
- Uses `gemini-flash-latest-non-thinking` model (do not change to thinking model)
- Prompts are embedded in `scraper.py:generate_report()`
- HTML template is mobile-optimized (390x844px viewport)
- Airport names loaded from `iata-icao.csv` for Chinese translation

### Important Constraints
1. **Virtual environment**: Create with `uv venv`, always activate `.venv` before running Python commands
2. **Always use uv**: Use `uv venv` to create venv, `uv pip install` for packages - never use `python -m venv` or `pip`
3. **No os.getenv()**: Use `load_config()` function only
4. **Data persistence**: `data/` folder is Docker volume-mounted for price history DB and graphs
5. **Chinese output**: All reports are generated in Chinese
6. **WebDriverWait disabled**: Using fixed time.sleep() instead due to Docker compatibility issues
