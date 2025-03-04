# Weather Brief App

This Python application retrieves and displays weather information (METAR and TAF) for a specified ICAO airport code and sends it to a Slack channel.

## Features

-   Fetches raw METAR and TAF data from aviationweather.gov.
-   Decodes METAR data into a human-readable format.
-   Validates ICAO airport codes.
-   Sends formatted weather briefings to a Slack channel using a webhook.
-   Includes error handling for network issues and invalid input.
-   Uses environment variables for sensitive information (Slack webhook URL).
-   Provides command-line interface.
-   Logs activity for debugging and monitoring.

## Prerequisites

-   Python 3.6 or higher
-   `requests` library (`pip install requests`)
-   `python-metar` library (`pip install python-metar`)
-   `python-dotenv` library (`pip install python-dotenv`)
-   A Slack workspace and a webhook URL.

## Usage

Run the application from the command line, providing the ICAO airport code as an argument:

```bash
python weather_brief.py KJFK