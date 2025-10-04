# AI Agent Specification for Air Ticket Search on tour.ne.jp

## 1. Project Overview

An autonomous AI agent that searches for air tickets on https://www.tour.ne.jp, analyzes flight results, and sends summarized recommendations via Telegram. The agent is configured via a `.env` file and can be triggered on demand.

## 2. System Architecture

### 2.1 Technology Stack
- **Language**: Python 3.11
- **Framework**: LangGraph (for agent orchestration)
- **Web Scraping**: Selenium with headless Chrome
- **AI Model**: Google Gemini Flash (for summary generation)
- **Messaging**: Telegram Bot API
- **Configuration**: python-dotenv
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
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Config  │→ │  Scraper │→ │ HTML Parser │→ │  Result  │→ │ Analyzer │ │
│  │  Loader  │  │   Node   │  │  (to JSON)  │  │  Logger  │  │ (Gemini) │ │
│  └──────────┘  └──────────┘  └─────────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Headless Chrome                             │
│           (Selenium WebDriver)                           │
└─────────────────────────────────────────────────────────┘
```

## 3. Configuration

The agent is configured using a single `.env` file. This file contains both secrets (like API keys) and search parameters. Using environment variables is a standard practice for containerized applications.

A `.env.sample` file is provided as a template. To run the agent, copy it to `.env` and fill in your secrets.

**`.env` file structure:**
```
# Secrets
TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
GEMINI_API_ENDPOINT="YOUR_GEMINI_API_ENDPOINT"

# Search Parameters
ORIGIN="TYO"
DESTINATIONS="CMB,BKK"
DEPARTURE_DATES="20251227,20251228"
AIR_TYPE="0"
RETURN_DATE=""
PASSENGERS="1"
```
- `DESTINATIONS` and `DEPARTURE_DATES` are comma-separated strings.
- `GEMINI_API_ENDPOINT` is an optional custom endpoint for the Gemini API.

## 4. URL Format Analysis

### 4.1 URL Structure
```
https://www.tour.ne.jp/w_air/list/?air_type=0&slice_info=TYO-CMB#dpt_date=20251227&page_from=index
```

### 4.2 URL Parameters Breakdown

| Parameter | Value | Description |
|-----------|-------|-------------|
| `air_type` | `0` | Flight type (0 = one-way, 1 = round-trip) |
| `slice_info` | `TYO-CMB` | Route (Origin-Destination airport codes) |
| `dpt_date` | `20251227` | Departure date (YYYYMMDD format) |
| `page_from` | `index` | Referrer page identifier |

## 5. Web Scraping and Data Extraction

### 5.1 Page Load Strategy
```
1. Navigate to URL
2. Wait for initial DOM load
3. Monitor network activity
4. Wait until all XHR/Fetch requests complete
5. Additional 2-second buffer for dynamic content rendering
6. Verify presence of target elements (flight-area divs)
```

### 5.2 Target HTML Elements

#### Primary Container
```html
<div class="flight-area Area_flight_area">
```

#### Key Data Points
The scraper will extract detailed information for each flight and structure it into a JSON object.

### 5.3 JSON Structure for LLM Analysis
After parsing the HTML, the flight data is converted into a structured JSON format. This JSON is then passed to the Gemini model for analysis.

**Example JSON for a single flight:**
```json
{
  "flight_id": "some_unique_identifier_from_html",
  "provider_name": "Gotogate",
  "price": {
    "total": 86394,
    "currency": "JPY"
  },
  "schedule": {
    "departure": {
      "airport": "NRT",
      "datetime": "2025-12-27T19:50:00"
    },
    "arrival": {
      "airport": "CMB",
      "datetime": "2025-12-28T23:40:00"
    },
    "duration_total": "31h 20m",
    "transfers_count": 4,
    "transfer_type": "self-transfer"
  },
  "airlines": [
    "济州航空",
    "Unknown Airline"
  ],
  "baggage": {
    "carry_on": true,
    "checked": true,
    "details": "Carry-on + Checked bag included"
  },
  "vendors": [
    {
      "name": "Gotogate",
      "price": 86394
    },
    {
      "name": "MyTrip",
      "price": 87100
    }
  ],
  "legs": [
    {
      "flight_number": "7C1105",
      "airline": "济州航空",
      "departure": { "airport": "NRT", "datetime": "2025-12-27T19:50" },
      "arrival": { "airport": "ICN", "datetime": "2025-12-27T22:40" },
      "duration": "2h 50m"
    },
    {
      "layover_duration": "3h 10m"
    }
  ]
}
```

## 6. LangGraph Agent Design

### 6.1 Agent State Schema
```python
class AgentState(TypedDict):
    search_configs: list[dict]   # List of search jobs from config
    current_search: dict         # The current search being processed
    raw_html: str                # Scraped HTML content
    parsed_flights: list[dict]   # Extracted flight data as JSON
    analysis_prompt: str         # Generated prompt for Gemini
    summary: str                 # AI-generated summary
    telegram_message: str        # Formatted message for Telegram
    debug_file_path: Optional[str] # Path to the saved debug file
    error: Optional[str]         # Error tracking
    metadata: dict               # Execution metadata
```

### 6.2 Graph Nodes

#### Node 1: Config Loader
**Purpose**: Load search jobs from the `.env` file.
**Input**: None.
**Output**: `search_configs` (a list of individual search queries).
**Logic**:
- Load environment variables from `.env`.
- Parse comma-separated strings for `DESTINATIONS` and `DEPARTURE_DATES`.
- For each combination of destination and departure date, create a search configuration object.
- Validate airport codes and date formats.

#### Node 2: URL Constructor
**Purpose**: Build search URL for the current search job.
**Input**: `current_search`.
**Output**: Formatted URL string.

#### Node 3: Web Scraper
**Purpose**: Fetch flight data from the generated URL.
**Input**: Search URL.
**Output**: `raw_html`.

#### Node 4: HTML Parser
**Purpose**: Extract structured JSON data from HTML.
**Input**: `raw_html`.
**Output**: `parsed_flights`.

#### Node 5: Result Logger
**Purpose**: Save the parsed flight data to a markdown file for debugging.
**Input**: `parsed_flights`, `current_search`.
**Output**: `debug_file_path`.
**Logic**:
- Create the `data/` directory if it doesn't exist.
- Generate a filename from the search parameters and timestamp (e.g., `data/TYO-CMB-20251227-1664803200.md`).
- Convert the `parsed_flights` list to a pretty-printed JSON string.
- Wrap the JSON string in a markdown code block.
- Write the content to the file and store the path in `debug_file_path`.

#### Node 6: Flight Analyzer
**Purpose**: Generate an AI-powered summary of the best flights.
**Input**: `parsed_flights`.
**Output**: `summary`.

#### Node 7: Message Formatter
**Purpose**: Format the summary for Telegram.
**Input**: `summary`.
**Output**: `telegram_message`.

#### Node 8: Telegram Sender
**Purpose**: Deliver results to the user.
**Input**: `telegram_message`.
**Output**: Delivery confirmation.

### 6.3 Graph Edges (Flow)
The agent will loop through each search job defined in the `.env` file.
```
START → Config Loader
  ↓
(For each search in search_configs)
  ↓
URL Constructor → Web Scraper → HTML Parser → Result Logger → Flight Analyzer → Message Formatter → Telegram Sender
  ↓ (on any error)
Error Handler → Telegram Sender (error message)
  ↓
(Next search or END)
```

## 7. Gemini Prompt Engineering

### 7.1 System Prompt Template
```
You are a professional travel assistant analyzing flight search results provided in JSON format.
Your task is to summarize the TOP 3 CHEAPEST flights in a clear, concise format in Chinese.

INPUT DATA:
```json
{json_flights_data}
```

REQUIREMENTS:
1. List exactly 3 flights (cheapest first).
2. For each flight include:
   - Total price (highlight the cheapest).
   - Airline(s).
   - Departure & arrival times (with dates).
   - Total duration.
   - Number of transfers.
   - Baggage allowance.
   - The primary vendor/provider.
3. Add a brief note if there are significant differences in layover times or transfer types (e.g., self-transfer).
4. Use emojis for visual clarity (✈️ 💰 ⏱️ 🎒).
5. Keep total response under 500 words.
6. Write in a friendly but professional tone.
7. **Output must be in Chinese.**

EXAMPLE FORMAT:
[表情] 航班 1: [航空公司] - ¥[价格]
📅 [日期] [时间] → [日期] [时间]
⏱️ [总时长] | 🔄 [中转次数]
🎒 [行李]
🏢 销售商: [名称]

[Repeat for 3 flights]

💡 备注: [任何重要的注意事项]
```

### 7.2 Gemini API Configuration
```python
gemini_config = {
    "model": "gemini-flash-latest", # Use a stable model name
    "temperature": 0.3,
    "top_p": 0.8,
    "max_output_tokens": 1024,
}
```

## 8. Telegram Bot Design

### 8.1 Bot Commands
The bot's primary role is to trigger the agent and report results.
```
/start - Welcome message and instructions.
/run - Trigger a new flight search based on the .env configuration.
/help - Show usage examples.
/status - Check the status of the current run.
```

### 8.2 Interaction Flow
```
User sends: /run
Bot replies: 🔍 Starting flight search based on your configuration... I will notify you when the results are ready.
[After processing all searches from .env]:
Bot sends: [Formatted summary for first search]
Bot sends: [Formatted summary for second search]
...
Bot sends: ✅ All searches complete.
```

## 9. Docker Configuration

### 9.1 Entrypoint Script (`entrypoint.sh`)
A simple shell script will be the entrypoint for the Docker container. It ensures that the main Python application is executed when the container starts.

```sh
#!/bin/sh
# /app/entrypoint.sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Run the main Python application
echo "Starting AI Air Ticket Agent..."
python /app/main.py
```

### 9.2 Multi-stage Dockerfile Structure
The `Dockerfile` will use a multi-stage build to create a lean final image.

```dockerfile
# Stage 1: Builder
FROM python:3.11-alpine AS builder
WORKDIR /app
RUN apk add --no-cache gcc musl-dev
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-alpine
WORKDIR /app
# Install runtime dependencies
RUN apk add --no-cache chromium chromium-chromedriver ca-certificates fonts-liberation

# Copy application code and dependencies
COPY --from=builder /root/.local /root/.local
COPY . .

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV CHROME_DRIVER_PATH=/usr/bin/chromedriver
ENV HEADLESS=true

# Make entrypoint executable and run it
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
```

### 9.3 Image Size Optimization
- Use `.dockerignore` to exclude `.git/`, `__pycache__/`, `*.pyc`, tests, and docs.
- Multi-stage build excludes build tools like `gcc`.
- Use `--no-cache-dir` for pip installs.

## 10. Python Package Requirements

### 10.1 Core Dependencies (`requirements.txt`)
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

# Logging
structlog>=23.2.0
```

### 10.2 Development Dependencies
```
pytest>=7.4.0
black>=23.12.0
ruff>=0.1.0
mypy>=1.7.0
```
