# AI Air Ticket Search Agent

An autonomous AI agent that searches for air tickets on `tour.ne.jp`, analyzes the results, and sends summarized recommendations in Chinese via Telegram.

## Features

- **Automated Search**: Scrapes flight data from `tour.ne.jp` for multiple destinations and dates.
- **AI-Powered Analysis**: Uses Google Gemini to analyze the flight options and generate a summary of the top 3 cheapest flights.
- **Telegram Notifications**: Delivers flight reports directly to you through a Telegram bot.
- **Configurable**: Easily configure search parameters (origin, destinations, dates) through a `.env` file.
- **Containerized**: Runs in a Docker container for consistent and easy deployment.

## Technology Stack

- **Language**: Python 3.11
- **AI Framework**: LangGraph, LangChain
- **AI Model**: Google Gemini
- **Web Scraping**: Selenium, BeautifulSoup4
- **Messaging**: Telegram Bot API
- **Containerization**: Docker

## Architecture

The agent uses a simple pipeline architecture orchestrated by LangGraph:

1.  **Config Loader**: Reads search parameters from the `.env` file.
2.  **Scraper**: Navigates a headless Chrome browser to scrape flight data.
3.  **HTML Parser**: Parses the raw HTML and converts it into structured JSON.
4.  **Analyzer**: Sends the JSON data to the Gemini model for analysis and summary.
5.  **Telegram Sender**: Formats the summary and sends it via the Telegram bot.

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
- `/run`: Triggers a new flight search based on the configuration in your `.env` file. The bot will notify you when the results are ready.
- `/help`: Shows usage examples.

## License

This project is licensed under the terms of the LICENSE file.
