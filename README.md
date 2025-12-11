# AI Air Ticket Search Agent

An autonomous AI agent that searches for air tickets on `tour.ne.jp`, analyzes the results, and sends visually appealing flight reports via Telegram.

## Features

- **Automated Search**: Scrapes flight data from `tour.ne.jp` for multiple destinations and dates.
- **AI-Powered Analysis**: Uses Google Gemini to analyze flight options and generate comprehensive reports.
- **Visual Reports**: Creates beautiful HTML reports and renders them as PNG images optimized for mobile viewing.
- **Telegram Notifications**: Delivers flight reports as images directly to your Telegram bot.
- **Mobile Optimized**: Reports are designed for optimal viewing on smartphones with portrait orientation.
- **Configurable**: Easily configure search parameters (origin, destinations, dates) through a `.env` file.
- **Containerized**: Runs in a Docker container with headless Chrome for consistent deployment.

## Technology Stack

- **Language**: Python 3.11
- **AI Framework**: LangGraph, LangChain
- **AI Model**: Google Gemini
- **Web Scraping**: Selenium with headless Chrome
- **Image Rendering**: Chrome headless screenshot capture
- **Messaging**: Telegram Bot API with photo support
- **Containerization**: Docker with Chrome/Chromium

## Architecture

The agent uses a sophisticated pipeline architecture orchestrated by LangGraph:

1.  **Config Loader**: Reads search parameters from the `.env` file.
2.  **Scraper**: Navigates a headless Chrome browser to scrape flight data.
3.  **HTML Parser**: Parses the raw HTML and converts it into structured JSON.
4.  **Report Generator**: Creates beautiful HTML reports using AI analysis.
5.  **Image Renderer**: Converts HTML reports to PNG images using headless Chrome.
6.  **Telegram Sender**: Sends the PNG images via Telegram bot with captions.

## Visual Report Features

- **Modern Design**: Beautiful gradient backgrounds and card-based layout
- **Mobile First**: Optimized for vertical viewing on smartphones (390x844px)
- **Responsive Layout**: Adapts to different screen sizes with touch-friendly interface
- **Professional Styling**: Modern typography and color schemes
- **Flight Cards**: Each flight displayed in an attractive card format
- **Complete Information**: Price, airline, flight numbers, duration, transfers, baggage info
- **Airport Details**: Full airport names with IATA codes

## Getting Started

### Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/get-started)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone <repository-url>
    cd ai_airticket
    ```

2.  **Configure the agent:**
    Create a `.env` file by copying the sample file:
    ```sh
    cp .env.sample .env
    ```
    Now, edit the `.env` file with your own values. You **must** provide your Telegram Bot Token and Gemini API Key.

    ```dotenv
    # Secrets - PLEASE FILL THESE IN
    TELEGRAM_BOT_TOKEN=""
    GEMINI_API_KEY=""

    # --- Search Parameters ---

    # Origin airport code (IATA format)
    ORIGIN="TYO"

    # A comma-separated list of destination airport codes to search for.
    DESTINATIONS="CMB,BKK"

    # A comma-separated list of departure dates to search for (YYYYMMDD format).
    DEPARTURE_DATES="20251227,20251228"

    # Flight type: 0 = one-way, 1 = round-trip
    AIR_TYPE="0"

    # Return date (YYYYMMDD format). Only used if air_type is 1.
    RETURN_DATE=""

    # Number of passengers
    PASSENGERS="1"
    ```

3.  **Build and run the Docker container:**
    ```sh
    docker build -t ai-air-ticket .
    docker run --env-file .env ai-air-ticket
    ```
    The agent will start, and you can interact with it via your Telegram bot.

## Usage

Interact with the agent through your Telegram bot using these commands:

- `/start`: Displays a welcome message and instructions.
- `/run`: Triggers a new flight search and sends visual reports as images.
- `/help`: Shows usage examples.

The agent will:
1. Search for flights based on your configuration
2. Analyze the results using AI
3. Generate beautiful HTML reports
4. Render them as PNG images optimized for mobile
5. Send the images to your Telegram channel

## Testing

Test the Chrome rendering functionality:
```bash
python test_chrome_rendering.py
```

Test the HTML report generation:
```bash
python test_html_report.py
```

## Recent Updates

- **Visual Reports**: HTML reports are now rendered as PNG images for better mobile viewing
- **Mobile Optimization**: Reports are optimized for smartphone portrait orientation
- **Image Delivery**: Flight reports are sent as images to Telegram instead of plain text
- **Chrome Integration**: Uses headless Chrome for HTML rendering in Docker environment
- **Fallback Support**: Falls back to text messages if image rendering fails

## License

This project is licensed under the terms of the LICENSE file.
