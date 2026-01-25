# Top Feeds Scraper

Scrapes the top feeds from LiveATC.net and caches them to JSON for the backend to serve.

## Quick Start

### 1. Install Dependencies

Using `uv` (recommended):
```bash
cd server/scraper
uv venv
source .venv/bin/activate
uv pip install -r requirements-playwright.txt
playwright install chromium
```

Or using `pip`:
```bash
cd server/scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-playwright.txt
playwright install chromium
```

### 2. Test the Scraper

Create mock data (no scraping):
```bash
python top_feeds_playwright.py --mock
```

Run once (real scraping):
```bash
python top_feeds_playwright.py
```

Run with visible browser (helps with Cloudflare):
```bash
python top_feeds_playwright.py --headed
```

### 3. Run as Daemon

Run continuously, scraping every 30 minutes:
```bash
python top_feeds_playwright.py --daemon --interval 30
```

## Running as a Service

### macOS (launchd)

1. Update paths in `com.lofi-atc.scraper.plist` to match your setup
2. Copy to LaunchAgents:
   ```bash
   cp com.lofi-atc.scraper.plist ~/Library/LaunchAgents/
   ```
3. Load the service:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.lofi-atc.scraper.plist
   ```
4. Check status:
   ```bash
   launchctl list | grep lofi-atc
   ```
5. View logs:
   ```bash
   tail -f scraper.log scraper.error.log
   ```
6. Stop the service:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.lofi-atc.scraper.plist
   ```

### Linux (systemd)

1. Update paths in `lofi-atc-scraper.service` to match your setup
2. Copy to systemd:
   ```bash
   sudo cp lofi-atc-scraper.service /etc/systemd/system/
   ```
3. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```
4. Start the service:
   ```bash
   sudo systemctl start lofi-atc-scraper
   ```
5. Enable on boot:
   ```bash
   sudo systemctl enable lofi-atc-scraper
   ```
6. Check status:
   ```bash
   sudo systemctl status lofi-atc-scraper
   ```
7. View logs:
   ```bash
   sudo journalctl -u lofi-atc-scraper -f
   ```

### Production Deployment

For production, consider:

1. **Cron Job (simplest)**:
   ```bash
   # Edit crontab
   crontab -e

   # Add line to run every 30 minutes
   */30 * * * * cd /opt/lofi-atc/server/scraper && .venv/bin/python top_feeds_playwright.py >> scraper.log 2>&1
   ```

2. **Docker Container**:
   - Use `mcr.microsoft.com/playwright/python:v1.40.0-jammy` as base image
   - Run as daemon in container with restart policy

3. **Serverless Function**:
   - Deploy as AWS Lambda / Google Cloud Function
   - Trigger on CloudWatch / Cloud Scheduler (every 30 min)
   - Write to shared volume or S3/GCS

## Troubleshooting

### Cloudflare Blocks Requests

If you get 403 errors:
- Use `--headed` flag to run with visible browser
- Increase `--interval` to scrape less frequently (60+ minutes)
- Use the manual JSON file approach instead

### Timeout Errors

If scraping times out:
- Check your internet connection
- LiveATC might be down or slow
- Try increasing timeout in the code
- Fall back to manual JSON file

### Manual Fallback

If scraping is unreliable, just maintain `../data/top_feeds.json` manually:

```json
{
  "updated_at": "2026-01-24T23:59:00Z",
  "feeds": [
    {
      "rank": 1,
      "feed_id": "kjfk_twr",
      "name": "New York JFK Tower",
      "listeners": 342,
      "stream_url": "http://d.liveatc.net/kjfk_twr"
    }
  ]
}
```

The backend reads this file directly, so scraping is optional.

## Output

The scraper writes to `../data/top_feeds.json` which the Rust backend serves via `/api/top-feeds`.
