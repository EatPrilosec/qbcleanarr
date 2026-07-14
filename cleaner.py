import configparser
import requests
import schedule
import time
import os
import logging
from typing import List, Dict

# Setup logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CONFIG_PATH = os.environ.get("CONFIG_PATH", "config.ini")

def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_PATH):
        logger.error(f"Configuration file not found at {CONFIG_PATH}")
        return config
    config.read(CONFIG_PATH)
    return config

def get_torrents(address: str, port: str, apikey: str, category: str) -> List[Dict]:
    url = f"http://{address}:{port}/api/v2/torrents/info"
    params = {
        "filter": "completed",
        "category": category
    }
    headers = {}
    if apikey:
        headers["Authorization"] = f"Bearer {apikey}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching torrents from {address}:{port} for category {category}: {e}")
        return []

def delete_torrents(address: str, port: str, apikey: str, hashes: List[str], delete_files: bool):
    if not hashes:
        return
    url = f"http://{address}:{port}/api/v2/torrents/delete"
    data = {
        "hashes": "|".join(hashes),
        "deleteFiles": str(delete_files).lower()
    }
    headers = {}
    if apikey:
        headers["Authorization"] = f"Bearer {apikey}"
        
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully deleted {len(hashes)} torrent(s) from {address}:{port}. (deleteFiles={delete_files})")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error deleting torrents from {address}:{port}: {e}")

def run_cleaner():
    logger.info("Running cleaner cycle...")
    config = load_config()
    if not config.sections():
        logger.warning("No sections found in config or config file missing.")
        return

    for section in config.sections():
        try:
            address = config.get(section, "address")
            
            # Clean up address if user included http:// or https://
            if address.startswith("http://"):
                address = address[7:]
            elif address.startswith("https://"):
                address = address[8:]
            address = address.rstrip("/")

            port = config.get(section, "port")
            apikey = config.get(section, "apikey", fallback="")
            categories_str = config.get(section, "categories", fallback="")
            cleanmode = config.get(section, "cleanmode", fallback="remove")
            
            delete_files = (cleanmode.lower() == "delete")
            
            categories = [c.strip() for c in categories_str.split(",") if c.strip()]
            if not categories:
                logger.warning(f"No categories defined for section '{section}'. Skipping.")
                continue

            for category in categories:
                torrents = get_torrents(address, port, apikey, category)
                to_delete = []
                
                logger.debug(f"[{section}] Fetched {len(torrents)} torrents for category '{category}'.")
                
                for t in torrents:
                    # state: pausedUP (completed and paused/not seeding) or completed
                    state = t.get("state", "")
                    name = t.get("name", "Unknown")
                    hash_id = t.get("hash")
                    
                    logger.debug(f"[{section}] Found torrent: {name} (State: {state})")
                    
                    # In qBittorrent, completed torrents that are not seeding are usually 'pausedUP' or 'stoppedUP' (newer versions)
                    if state in ["pausedUP", "stoppedUP"]:
                        to_delete.append(hash_id)
                        logger.info(f"[{section}] Marking for deletion: {name} (State: {state})")
                
                if to_delete:
                    delete_torrents(address, port, apikey, to_delete, delete_files)
                else:
                    logger.debug(f"[{section}] No eligible torrents found to clean for category {category}.")
                    
        except Exception as e:
            logger.error(f"Error processing section '{section}': {e}")

if __name__ == "__main__":
    logger.info("Starting qbcleanarr...")
    run_interval = int(os.environ.get("RUN_INTERVAL_MINUTES", "5"))
    
    # Run once at startup
    run_cleaner()
    
    # Schedule to run periodically
    schedule.every(run_interval).minutes.do(run_cleaner)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
