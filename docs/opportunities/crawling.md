# Crawler Architecture & Connector Framework

## Connectors
- `HTMLConnector`: Direct web page scraping with SafeFetcher.
- `RSSConnector`: RSS and Atom feed document extraction.
- `SitemapConnector`: XML Sitemap parsing and sub-link discovery.
- `JSONConnector`: Static JSON payload and feed processing.
- `APIConnector`: REST API ingestion handler.
- `PDFConnector`: PDF official notice extraction.

## Compliance & Rate Limiting
- **Robots Policy (`robots.py`)**: Parses and enforces domain `robots.txt` guidelines.
- **Domain Rate Limiter (`rate_limiter.py`)**: Sliding-window rate limiting per domain.
- **SSRF Protection (`SafeFetcher`)**: Blocks private IP addresses (`127.0.0.1`, `localhost`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`).
