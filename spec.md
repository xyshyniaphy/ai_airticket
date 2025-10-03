# AI Agent Specification for Air Ticket Search on tour.ne.jp

## 1. Project Overview

An autonomous AI agent that searches for air tickets on https://www.tour.ne.jp, analyzes flight results, and sends summarized recommendations via Telegram.

## 2. System Architecture

### 2.1 Technology Stack
- **Language**: Python 3.11
- **Framework**: LangGraph (for agent orchestration)
- **Web Scraping**: Selenium with headless Chrome
- **AI Model**: Google Gemini Flash (for summary generation)
- **Messaging**: Telegram Bot API
- **Containerization**: Docker (Alpine-based multi-stage build)

### 2.2 Component Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Bot                          │
│                  (Trigger & Output)                      │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                  LangGraph Agent                         │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │   Input    │→ │  Scraper   │→ │    Analyzer      │  │
│  │  Parser    │  │   Node     │  │   (Gemini)       │  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Headless Chrome                             │
│           (Selenium WebDriver)                           │
└─────────────────────────────────────────────────────────┘
```

## 3. URL Format Analysis

### 3.1 URL Structure
```
https://www.tour.ne.jp/w_air/list/?air_type=0&slice_info=TYO-CMB#dpt_date=20251227&page_from=index
```

### 3.2 URL Parameters Breakdown

| Parameter | Value | Description |
|-----------|-------|-------------|
| `air_type` | `0` | Flight type (0 = one-way, likely 1 = round-trip) |
| `slice_info` | `TYO-CMB` | Route (Origin-Destination airport codes) |
| `dpt_date` | `20251227` | Departure date (YYYYMMDD format) |
| `page_from` | `index` | Referrer page identifier |

### 3.3 Configurable Search Parameters
```python
search_config = {
    "origin": str,        # e.g., "TYO" (Tokyo)
    "destination": str,   # e.g., "CMB" (Colombo)
    "departure_date": str,# e.g., "20251227"
    "air_type": int,      # 0 = one-way, 1 = round-trip
    "return_date": str    # Optional, for round-trip
}
```

## 4. Web Scraping Strategy

### 4.1 Page Load Strategy
```
1. Navigate to URL
2. Wait for initial DOM load
3. Monitor network activity
4. Wait until all XHR/Fetch requests complete
5. Additional 2-second buffer for dynamic content rendering
6. Verify presence of target elements (flight-area divs)
```

### 4.2 Network Idle Detection
- Monitor Chrome DevTools Protocol network events
- Define "idle" as no network activity for 500ms
- Maximum wait timeout: 60 seconds
- Fallback: Check for presence of `.flight-area` elements

### 4.3 Target HTML Elements

#### Primary Container
```html
<div class="flight-area Area_flight_area">
```

#### Key Data Points to Extract

**Per Flight Card:**

1. **Flight Schedule (`sch-area`)**
   - Trip type: `sch-header` → text content
   - Airline names: `sch-header` → airline logos and text
   - Departure: `going-area` → date, time, airport code
   - Arrival: `return-area` → date, time, airport code
   - Duration: `flt-term` → total travel time
   - Transfers: `flt-term` → number of connections

2. **Price Information (`flight-summary`)**
   - Provider: `flight-summary-hdg` → text
   - Total price: `flight-summary-total` → numeric value
   - Price includes: taxes/fees indicator
   - Baggage: `flight-summary-info-list` → allowances

3. **Detailed Itinerary (from tooltip)**
   - Individual leg details: `custom-tip-container dl` elements
   - Flight numbers, aircraft types, layover times

4. **Multiple Vendors (from modal)**
   - Extract all vendors from `res-agt-list li` elements
   - Each vendor's specific price
   - Payment methods
   - Booking conditions

### 4.4 Data Attributes to Capture
```python
data_points = {
    "data-stab_flight": "Flight identifier",
    "data-airport-code": "Airport codes",
    "data-airline-code": "Airline identifiers",
    # Additional tracking attributes for debugging
}
```

## 5. LangGraph Agent Design

### 5.1 Agent State Schema
```python
class AgentState(TypedDict):
    search_params: dict          # User input parameters
    raw_html: str                # Scraped HTML content
    parsed_flights: list[dict]   # Extracted flight data
    analysis_prompt: str         # Generated prompt for Gemini
    summary: str                 # AI-generated summary
    telegram_message: str        # Formatted message for Telegram
    error: Optional[str]         # Error tracking
    metadata: dict               # Execution metadata
```

### 5.2 Graph Nodes

#### Node 1: Input Validator
**Purpose**: Validate and normalize user input
**Input**: Raw search parameters from Telegram
**Output**: Validated `search_params`
**Logic**:
- Validate airport codes (3-letter IATA)
- Validate date format and future dates
- Check required parameters
- Set defaults for optional parameters

#### Node 2: URL Constructor
**Purpose**: Build search URL
**Input**: `search_params`
**Output**: Formatted URL string
**Logic**:
- Construct URL with proper encoding
- Handle one-way vs round-trip logic

#### Node 3: Web Scraper
**Purpose**: Fetch flight data
**Input**: Search URL
**Output**: `raw_html`
**Logic**:
- Initialize headless Chrome
- Navigate and wait for network idle
- Extract page source
- Handle timeouts and errors
- Retry logic (max 3 attempts)

#### Node 4: HTML Parser
**Purpose**: Extract structured data
**Input**: `raw_html`
**Output**: `parsed_flights`
**Logic**:
- Parse all `.flight-area` elements
- Extract each flight's details
- Structure data into flight objects
- Sort by price (ascending)

#### Node 5: Flight Analyzer
**Purpose**: Generate AI summary
**Input**: `parsed_flights`
**Output**: `summary`
**Logic**:
- Select top 3 cheapest flights
- Generate structured prompt for Gemini
- Call Gemini Flash API
- Parse and validate response

#### Node 6: Message Formatter
**Purpose**: Format for Telegram
**Input**: `summary`
**Output**: `telegram_message`
**Logic**:
- Apply Telegram markdown formatting
- Add emojis for readability
- Include metadata (search params, timestamp)
- Truncate if exceeds Telegram limits

#### Node 7: Telegram Sender
**Purpose**: Deliver results
**Input**: `telegram_message`
**Output**: Delivery confirmation
**Logic**:
- Send via Telegram Bot API
- Handle rate limits
- Confirm delivery

### 5.3 Graph Edges (Flow)
```
START → Input Validator → URL Constructor → Web Scraper → HTML Parser
  ↓
HTML Parser → Flight Analyzer → Message Formatter → Telegram Sender → END
  ↓ (on error)
Error Handler → Telegram Sender (error message) → END
```

### 5.4 Conditional Edges
- **After Scraper**: If no data found → Retry (max 3) or Error Handler
- **After Parser**: If < 3 flights found → Continue with available data
- **After Analyzer**: If Gemini fails → Use fallback template summary

## 6. Data Models

### 6.1 Flight Object Schema
```python
@dataclass
class Flight:
    flight_id: str
    airline_primary: str
    airlines_all: list[str]
    
    # Schedule
    departure_date: str
    departure_time: str
    departure_airport: str
    arrival_date: str
    arrival_time: str
    arrival_airport: str
    
    # Details
    duration_total: str
    transfers_count: int
    transfer_type: str  # e.g., "self-transfer"
    
    # Price
    provider_name: str
    price_total: int
    price_currency: str
    price_includes: list[str]  # taxes, fees, baggage
    
    # Baggage
    carry_on_included: bool
    checked_baggage_included: bool
    
    # All vendors
    all_vendors: list[dict]  # [{name, price, url}, ...]
    
    # Itinerary
    legs: list[dict]  # Detailed leg-by-leg breakdown
```

### 6.2 Search Parameters Model
```python
@dataclass
class SearchParams:
    origin: str
    destination: str
    departure_date: str
    air_type: int = 0  # 0=one-way, 1=round-trip
    return_date: Optional[str] = None
    passengers: int = 1
```

## 7. Gemini Prompt Engineering

### 7.1 System Prompt Template
```
You are a professional travel assistant analyzing flight search results.
Your task is to summarize the TOP 3 CHEAPEST flights in a clear, concise format.

INPUT DATA:
{json_flights_data}

REQUIREMENTS:
1. List exactly 3 flights (cheapest first)
2. For each flight include:
   - Total price (highlight the cheapest)
   - Airline(s)
   - Departure & arrival times (with dates)
   - Total duration
   - Number of transfers
   - Baggage allowance
   - Provider name
3. Add a brief note if there are significant differences in layover times
4. Use emojis for visual clarity (✈️ 💰 ⏱️ 🎒)
5. Keep total response under 500 words
6. Write in a friendly but professional tone
7. Output in Japanese (the website is in Japanese)

FORMAT:
[Emoji] Flight 1: [Airline] - ¥[Price]
📅 [Date] [Time] → [Date] [Time]
⏱️ [Duration] | 🔄 [Transfers]
🎒 [Baggage]
🏢 Provider: [Name]

[Repeat for 3 flights]

💡 Quick Note: [Any important observations]
```

### 7.2 Gemini API Configuration
```python
gemini_config = {
    "model": "gemini-2.0-flash-exp",
    "temperature": 0.3,  # Lower for consistency
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 1024,
    "safety_settings": {
        # Adjust as needed
    }
}
```

## 8. Telegram Bot Design

### 8.1 Bot Commands
```
/start - Welcome message and instructions
/search [origin] [dest] [date] - Search flights
/help - Show usage examples
/cancel - Cancel current operation
```

### 8.2 Input Format
```
User sends: /search TYO CMB 20251227
Bot replies: 🔍 Searching flights from Tokyo to Colombo on Dec 27, 2025...
[After processing]: [Formatted summary]
```

### 8.3 Message Format Example
```
✈️ TOP 3 CHEAPEST FLIGHTS: Tokyo → Colombo

━━━━━━━━━━━━━━━━━━━━━
💰 Flight 1: ¥86,394 (BEST PRICE)
🛫 チェジュ航空 + 1 other
📅 12/27 19:50 (NRT) → 12/28 23:40 (CMB)
⏱️ 31h 20m | 🔄 4 transfers (self)
🎒 Carry-on + Checked bag included
🏢 Provider: Gotogate

━━━━━━━━━━━━━━━━━━━━━
💰 Flight 2: ¥[Price]
[Similar format]

━━━━━━━━━━━━━━━━━━━━━
💰 Flight 3: ¥[Price]
[Similar format]

━━━━━━━━━━━━━━━━━━━━━
💡 Note: Flight 1 has 4 self-transfers; consider layover times.

🔗 View all results: [Link to tour.ne.jp search]
⏰ Searched at: 2025-01-XX XX:XX JST
```

### 8.4 Error Messages
```
❌ No flights found for these criteria
❌ Invalid date format (use YYYYMMDD)
❌ Invalid airport code
❌ Service temporarily unavailable, please try again
```

## 9. Docker Configuration

### 9.1 Multi-stage Dockerfile Structure

```dockerfile
# Stage 1: Builder
FROM python:3.11-alpine AS builder
# Install build dependencies
# Install Python packages
# Compile/optimize dependencies

# Stage 2: Runtime
FROM python:3.11-alpine
# Install only runtime dependencies (Chrome, drivers)
# Copy only necessary files from builder
# Set up non-root user
# Configure entrypoint
```

### 9.2 Image Size Optimization
- Use `.dockerignore` to exclude:
  - `.git/`, `__pycache__/`, `*.pyc`
  - Test files, documentation
  - Development dependencies
- Multi-stage build to exclude build tools
- Strip unnecessary binaries
- Use `--no-cache-dir` for pip installs

### 9.3 Required System Packages
```
# Runtime
- chromium
- chromium-chromedriver
- ca-certificates
- fonts-liberation (for proper rendering)

# Build only (not in final image)
- gcc
- musl-dev
- python3-dev
```

### 9.4 Environment Variables
```
TELEGRAM_BOT_TOKEN=<secret>
GEMINI_API_KEY=<secret>
LOG_LEVEL=INFO
CHROME_DRIVER_PATH=/usr/bin/chromedriver
HEADLESS=true
MAX_RETRIES=3
NETWORK_IDLE_TIMEOUT=60
```

## 10. Python Package Requirements

### 10.1 Core Dependencies
```
# Agent framework
langgraph>=0.0.40
langchain>=0.1.0
langchain-google-genai>=0.0.6

# Web scraping
selenium>=4.15.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# API clients
python-telegram-bot>=20.7
google-generativeai>=0.3.0

# Utilities
pydantic>=2.5.0
python-dotenv>=1.0.0
httpx>=0.25.0

# Logging & monitoring
structlog>=23.2.0
```

### 10.2 Development Dependencies (excluded from image)
```
pytest>=7.4.0
black>=23.12.0
ruff>=0.1.0
mypy>=1.7.0
```

## 11. Error Handling Strategy

### 11.1 Retry Logic
- **Network errors**: 3 retries with exponential backoff (2s, 4s, 8s)
- **Page load timeout**: 2 retries, then report error
- **Gemini API errors**: 2 retries, fallback to
