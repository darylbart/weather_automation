import requests
import argparse
import xml.etree.ElementTree as ET
from metar.Metar import Metar
import logging
import re
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Set up Slack Webhook URL from environment variables
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_valid_icao(icao: str) -> bool:
    """Checks if the given string is a valid ICAO code."""
    return bool(re.match(r"^[A-Z]{4}$", icao))

def get_metar(icao: str) -> str:
    """Fetches raw METAR data for the given ICAO code."""
    if not is_valid_icao(icao):
        return "Invalid ICAO code."
    url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=raw"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        if response.text.strip():
            return response.text.strip()
        else:
            return "METAR data not available (empty response)."
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching METAR: {e}")
        return "METAR data not available (network error)."

def decode_metar(metar: str) -> str:
    """Decodes the METAR data into a human-readable format."""
    if "METAR data not available." in metar or "Invalid ICAO code." in metar:
        return metar
    try:
        parsed_metar = Metar(metar)
        return parsed_metar.string()
    except Exception as e:
        logging.error(f"Error decoding METAR: {e}")
        return "Error decoding METAR."

def get_taf(icao: str) -> str:
    """Fetches raw TAF data for the given ICAO code."""
    if not is_valid_icao(icao):
        return "Invalid ICAO code."
    url = f"https://aviationweather.gov/cgi-bin/data/dataserver.php?requestType=retrieve&dataSource=tafs&format=xml&stationString={icao}&hours=24"
    try:
        response = requests.get(url)
        response.raise_for_status()
        if not response.text.strip():
            return "TAF data not available (empty response)."
        root = ET.fromstring(response.text)
        taf_texts = [taf.text for taf in root.findall(".//TAF/text")]
        return "\n".join(taf_texts) if taf_texts else "TAF data not available."
    except (requests.exceptions.RequestException, ET.ParseError) as e:
        logging.error(f"Error fetching/parsing TAF: {e}")
        return "TAF data not available."

def send_to_slack(message: str, icao: str) -> None:
    """Send the weather data to Slack using the webhook with styling and emojis."""
    if SLACK_WEBHOOK_URL:
        payload = {
            "text": f"*Weather Brief for {icao.upper()}* :airplane: \n\n"
                    f"*METAR* :bar_chart: \n{message['metar']}\n\n"
                    f"*TAF* :cloud_with_rain: \n{message['taf']}\n\n"
                    f"*Decoded METAR* :book: \n{message['decoded_metar']}",
            "attachments": [
                {
                    "color": "#36a64f",  # Green color for the header
                    "title": "Weather Information",
                    "pretext": f"Weather Brief for *{icao.upper()}*",
                    "fields": [
                        {
                            "title": "METAR",
                            "value": message['metar'],
                            "short": False
                        },
                        {
                            "title": "TAF",
                            "value": message['taf'],
                            "short": False
                        },
                        {
                            "title": "Decoded METAR",
                            "value": message['decoded_metar'],
                            "short": False
                        }
                    ],
                    "footer": "Weather data provided by AviationWeather.gov",
                    "footer_icon": "https://www.aviationweather.gov/sites/default/files/favicon.ico",
                    "thumb_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Weather_icon_001.svg/120px-Weather_icon_001.svg.png"  # Example thumbnail icon
                }
            ]
        }

        try:
            response = requests.post(SLACK_WEBHOOK_URL, json=payload)
            response.raise_for_status()  # Raise an exception for bad responses
            logging.info("Data sent to Slack successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending data to Slack: {e}")
    else:
        logging.error("Slack Webhook URL not found in environment variables.")

def get_weather_brief(icao: str) -> None:
    """Fetches and displays weather brief for the given ICAO code."""
    logging.info(f"Fetching weather briefing for {icao.upper()}...")
    metar = get_metar(icao)
    taf = get_taf(icao)
    decoded_metar = decode_metar(metar)

    # Prepare message for Slack with more structured content
    message = {
        "metar": metar,
        "taf": taf,
        "decoded_metar": decoded_metar
    }
    
    # Print the data (for local view)
    print(f"\n*Weather Brief for {icao.upper()}*\n")
    print(f"*METAR:*\n{metar}")
    print(f"\n*TAF:*\n{taf}")
    print(f"\n*Decoded METAR:*\n{decoded_metar}")
    
    send_to_slack(message, icao)  # Send the formatted message to Slack

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get a full weather brief for an airport.")
    parser.add_argument("icao", type=str, help="ICAO code of the airport (e.g., KJFK, EGLL, FAOR)")
    args = parser.parse_args()
    get_weather_brief(args.icao)
