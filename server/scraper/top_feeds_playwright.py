#!/usr/bin/env python3
"""
Top Feeds Scraper for LiveATC using Playwright (real browser automation)

Uses Playwright to bypass Cloudflare by running a real headless Chrome browser.
"""

import argparse
import json
import logging
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
LIVEATC_TOP_FEEDS_URL = "https://www.liveatc.net/topfeeds.php"
DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / "data" / "top_feeds.json"
MAX_FEEDS = 5


def scrape_with_playwright(url, timeout_ms=60000, headless=True):
    """Scrape using Playwright with a real browser."""
    logger.info(f"Launching browser to fetch {url} (headless={headless})")

    with sync_playwright() as p:
        # Launch with more realistic settings
        browser = p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            # Add extra HTTP headers
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
        )

        page = context.new_page()

        try:
            # Navigate with less strict wait condition
            logger.info("Navigating to page...")
            page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)

            # Wait for the page to settle
            logger.info("Waiting for page to load...")
            page.wait_for_timeout(5000)

            # Check if we got a Cloudflare challenge page
            if 'challenge' in page.content().lower() or 'cloudflare' in page.title().lower():
                logger.warning("Cloudflare challenge detected, waiting longer...")
                page.wait_for_timeout(10000)

            # Try to wait for actual content (table with feeds)
            try:
                page.wait_for_selector('table', timeout=10000)
                logger.info("Found table element")
            except PlaywrightTimeout:
                logger.warning("No table found, proceeding anyway...")

            html = page.content()
            logger.info(f"Successfully fetched {len(html)} bytes")

            # Check if we actually got content or just a challenge page
            if len(html) < 1000:
                logger.warning("Page content seems too small, might be blocked")

            return html
        finally:
            browser.close()


def parse_top_feeds(html):
    """Parse the top feeds from the HTML page."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')
    feeds = []

    # Debug: save HTML to file for inspection
    debug_file = Path(__file__).parent / 'debug_page.html'
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    logger.info(f"Saved HTML to {debug_file} for debugging")

    # Find the topTable specifically
    top_table = soup.find('table', class_='topTable')
    if not top_table:
        logger.error("Could not find table with class 'topTable'")
        return []

    logger.info("Found topTable")

    # Find all feed entries in the topTable
    rows = top_table.find_all('tr')
    logger.info(f"Found {len(rows)} rows in topTable")

    # Try multiple patterns for feed links
    feed_patterns = [
        r'feedindex\.php\?feed=',
        r'play\.php\?mount=',
        r'\?icao=',
    ]

    for i, row in enumerate(rows):
        cells = row.find_all('td')

        # Need at least 3 cells: rank (index 0), listeners (index 1), feed info (index 2+)
        if len(cells) < 3:
            continue

        # Look for any links in the row
        links = row.find_all('a')
        feed_link = None

        for pattern in feed_patterns:
            feed_link = row.find('a', href=re.compile(pattern))
            if feed_link:
                logger.debug(f"Row {i}: Found link with pattern {pattern}")
                break

        if not feed_link:
            # Try any link that looks like it might be a feed
            for link in links:
                href = link.get('href', '')
                if 'feed' in href.lower() or 'mount' in href.lower():
                    feed_link = link
                    logger.debug(f"Row {i}: Found link by keyword: {href}")
                    break

        if not feed_link:
            continue

        # Extract feed_id from the href
        href = feed_link.get('href', '')

        # Try different parameter names
        feed_id = None
        for param in ['feed', 'mount', 'icao']:
            match = re.search(rf'{param}=([^&\s]+)', href)
            if match:
                feed_id = match.group(1)
                logger.debug(f"Row {i}: Extracted feed_id={feed_id} from param={param}")
                break

        if not feed_id:
            logger.debug(f"Row {i}: No feed_id found in {href}")
            continue

        # Get the feed name from the link text
        name = feed_link.get_text(strip=True)
        if not name:
            # Try getting text from the cell
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                if cell_text and not cell_text.isdigit():
                    name = cell_text
                    break

        if not name:
            logger.debug(f"Row {i}: No name found")
            continue

        # Get listener count from second column (index 1)
        listeners = 0
        listener_text = cells[1].get_text(strip=True).replace(',', '')
        if listener_text.isdigit():
            listeners = int(listener_text)
            logger.debug(f"Row {i}: Found listeners={listeners} in column 1")
        else:
            logger.debug(f"Row {i}: Column 1 is not a valid number: '{listener_text}'")

        # Build stream URL
        stream_url = f"http://d.liveatc.net/{feed_id}"

        logger.info(f"Row {i}: Found feed: {name} ({feed_id}) with {listeners} listeners")

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
    for feed in feeds:
        logger.info(f"  #{feed['rank']}: {feed['name']} ({feed['listeners']} listeners)")

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


def scrape_top_feeds(output_path, headless=True):
    """Main scraping function."""
    try:
        html = scrape_with_playwright(LIVEATC_TOP_FEEDS_URL, headless=headless)
        feeds = parse_top_feeds(html)

        if not feeds:
            logger.warning("No feeds parsed from page")
            return False

        write_feeds_to_file(feeds, output_path)
        return True

    except PlaywrightTimeout as e:
        logger.error(f"Timeout while loading page: {e}")
        return False
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        return False


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


def run_scheduler(output_path, interval_minutes, headless=True):
    """Run the scraper on a schedule with jitter."""
    import random

    logger.info(f"Starting scheduler with {interval_minutes} minute interval")

    while True:
        # Add random jitter (0-60 seconds) to avoid detection patterns
        jitter = random.uniform(0, 60)
        logger.info(f"Adding {jitter:.1f}s jitter before scrape")
        time.sleep(jitter)

        scrape_top_feeds(output_path, headless=headless)

        # Sleep until next interval
        sleep_seconds = interval_minutes * 60
        logger.info(f"Sleeping for {interval_minutes} minutes")
        time.sleep(sleep_seconds)


def main():
    parser = argparse.ArgumentParser(description='Scrape LiveATC top feeds with Playwright')
    parser.add_argument(
        '--output',
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help=f'Output JSON file path (default: {DEFAULT_OUTPUT_PATH})'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Create mock data instead of scraping (for testing)'
    )
    parser.add_argument(
        '--headed',
        action='store_true',
        help='Run browser in headed mode (visible, helps with Cloudflare)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Scrape interval in minutes (default: 30)'
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon with scheduled scraping'
    )

    args = parser.parse_args()

    if args.mock:
        success = create_mock_data(args.output)
        sys.exit(0 if success else 1)
    elif args.daemon:
        try:
            run_scheduler(args.output, args.interval, headless=not args.headed)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            sys.exit(0)
    else:
        success = scrape_top_feeds(args.output, headless=not args.headed)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
