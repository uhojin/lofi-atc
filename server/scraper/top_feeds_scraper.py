#!/usr/bin/env python3
"""
Top Feeds Scraper for LiveATC

Scrapes the top feeds from LiveATC using cloudscraper to bypass Cloudflare.
Writes results to a JSON file for the Rust backend to serve.
"""

import argparse
import json
import logging
import os
import random
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import cloudscraper
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
LIVEATC_TOP_FEEDS_URL = "https://www.liveatc.net/topfeeds.php"
DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / "data" / "top_feeds.json"
DEFAULT_INTERVAL_MINUTES = 5
MAX_FEEDS = 5
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10


def create_scraper():
    """Create a cloudscraper session with browser impersonation."""
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        },
        delay=10,
        captcha={
            'provider': '2captcha'
        }
    )

    # Set realistic headers
    scraper.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    })

    return scraper


def fetch_top_feeds_page(scraper):
    """Fetch the top feeds page HTML."""
    logger.info(f"Fetching top feeds from {LIVEATC_TOP_FEEDS_URL}")

    try:
        response = scraper.get(LIVEATC_TOP_FEEDS_URL, timeout=30)
        logger.info(f"Response status: {response.status_code}")
        response.raise_for_status()
        logger.info(f"Successfully fetched {len(response.text)} bytes")
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch page: {e}")
        logger.error(f"Response headers: {getattr(response, 'headers', 'N/A')}")
        raise


def parse_top_feeds(html):
    """Parse the top feeds from the HTML page."""
    soup = BeautifulSoup(html, 'html.parser')
    feeds = []

    # Find all feed entries in the table
    # LiveATC uses a table structure with feed info
    rows = soup.find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        # Look for links that go to feed pages
        link = row.find('a', href=re.compile(r'feedindex\.php\?feed='))
        if not link:
            continue

        # Extract feed_id from the href
        href = link.get('href', '')
        feed_match = re.search(r'feed=([^&]+)', href)
        if not feed_match:
            continue

        feed_id = feed_match.group(1)

        # Get the feed name from the link text
        name = link.get_text(strip=True)
        if not name:
            continue

        # Find listener count - usually in a cell with just a number
        listeners = 0
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            # Look for a cell that contains just a number (listener count)
            if cell_text.isdigit():
                listeners = int(cell_text)
                break

        # Build stream URL
        stream_url = f"http://d.liveatc.net/{feed_id}"

        feeds.append({
            'feed_id': feed_id,
            'name': name,
            'listeners': listeners,
            'stream_url': stream_url
        })

    # Sort by listeners descending and take top MAX_FEEDS
    feeds.sort(key=lambda x: x['listeners'], reverse=True)
    feeds = feeds[:MAX_FEEDS]

    # Add rank
    for i, feed in enumerate(feeds, 1):
        feed['rank'] = i

    logger.info(f"Parsed {len(feeds)} top feeds")
    return feeds


def write_feeds_to_file(feeds, output_path):
    """Write feeds to JSON file atomically."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'feeds': feeds
    }

    # Write to temp file first, then atomic rename
    temp_fd, temp_path = tempfile.mkstemp(
        dir=output_path.parent,
        prefix='.top_feeds_',
        suffix='.json'
    )

    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(data, f, indent=2)

        # Atomic rename
        os.replace(temp_path, output_path)
        logger.info(f"Wrote {len(feeds)} feeds to {output_path}")
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def scrape_top_feeds(output_path):
    """Main scraping function with retries."""
    scraper = create_scraper()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            html = fetch_top_feeds_page(scraper)
            feeds = parse_top_feeds(html)

            if not feeds:
                logger.warning("No feeds parsed from page")
                raise ValueError("No feeds found in page")

            write_feeds_to_file(feeds, output_path)
            return True

        except Exception as e:
            logger.error(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY_SECONDS * attempt
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

    logger.error("All retry attempts failed")
    return False


def run_scheduler(output_path, interval_minutes):
    """Run the scraper on a schedule with jitter."""
    logger.info(f"Starting scheduler with {interval_minutes} minute interval")

    while True:
        # Add random jitter (0-60 seconds) to avoid detection patterns
        jitter = random.uniform(0, 60)
        logger.info(f"Adding {jitter:.1f}s jitter before scrape")
        time.sleep(jitter)

        scrape_top_feeds(output_path)

        # Sleep until next interval
        sleep_seconds = interval_minutes * 60
        logger.info(f"Sleeping for {interval_minutes} minutes")
        time.sleep(sleep_seconds)


def create_mock_data(output_path):
    """Create mock top feeds data for testing."""
    mock_feeds = [
        {
            'rank': 1,
            'feed_id': 'kjfk_twr',
            'name': 'New York JFK Tower',
            'listeners': 342,
            'stream_url': 'http://d.liveatc.net/kjfk_twr'
        },
        {
            'rank': 2,
            'feed_id': 'klax_twr',
            'name': 'Los Angeles LAX Tower',
            'listeners': 287,
            'stream_url': 'http://d.liveatc.net/klax_twr'
        },
        {
            'rank': 3,
            'feed_id': 'kord_twr',
            'name': 'Chicago ORD Tower',
            'listeners': 215,
            'stream_url': 'http://d.liveatc.net/kord_twr'
        },
        {
            'rank': 4,
            'feed_id': 'katl_app',
            'name': 'Atlanta ATL Approach',
            'listeners': 198,
            'stream_url': 'http://d.liveatc.net/katl_app'
        },
        {
            'rank': 5,
            'feed_id': 'kdfw_twr',
            'name': 'Dallas DFW Tower',
            'listeners': 176,
            'stream_url': 'http://d.liveatc.net/kdfw_twr'
        }
    ]
    write_feeds_to_file(mock_feeds, output_path)
    logger.info("Created mock data for testing")
    return True


def main():
    parser = argparse.ArgumentParser(description='Scrape LiveATC top feeds')
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (no scheduling)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help=f'Output JSON file path (default: {DEFAULT_OUTPUT_PATH})'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=DEFAULT_INTERVAL_MINUTES,
        help=f'Scrape interval in minutes (default: {DEFAULT_INTERVAL_MINUTES})'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Create mock data instead of scraping (for testing)'
    )

    args = parser.parse_args()

    if args.mock:
        success = create_mock_data(args.output)
        sys.exit(0 if success else 1)
    elif args.once:
        success = scrape_top_feeds(args.output)
        sys.exit(0 if success else 1)
    else:
        try:
            run_scheduler(args.output, args.interval)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            sys.exit(0)


if __name__ == '__main__':
    main()
