# Shopify Auto Checkout System

## Overview

This is a Python-based automated Shopify checkout system designed for credit card validation and testing. The system processes cards through real Shopify store checkouts to verify card validity, using concurrent workers, proxy rotation, and site rotation for high-volume processing.

**Core Purpose:** Validate credit cards by attempting small purchases on Shopify stores, categorizing results as charged, live, declined, or requiring challenge (3D Secure/CAPTCHA).

**Key Capabilities:**
- Single card checking (`/sx` command)
- Mass card checking with 4 concurrent workers (`/msx` command)
- Site rotation across 90+ Shopify stores
- Proxy rotation with PureVPN proxies
- Real-time result categorization to output files
- Telegram bot integration for remote operation

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Processing Pipeline

The checkout flow follows these steps:
1. **Product Discovery** - Scans Shopify store's `/products.json` endpoint to find cheapest available product
2. **Cart Creation** - Adds product to cart via Shopify's cart API
3. **Checkout Initialization** - Creates checkout session with shipping/billing details
4. **Payment Session** - Generates payment method via Shopify's GraphQL API
5. **Payment Submission** - Submits card for processing
6. **Result Polling** - Polls for receipt status to determine outcome

### Concurrency Model

- Uses `asyncio` for asynchronous operations
- 4 concurrent worker tasks process cards in parallel
- Each worker maintains independent HTTP sessions via `httpx`
- Thread-safe state management with `asyncio.Lock`

### State Management

The `ShopifyGlobalState` class manages:
- **Site Pool:** `deque` of available Shopify sites for rotation
- **Banned Sites:** Permanently failed sites (CAPTCHA, errors) never reused
- **Proxy Pool:** Rotating list of authenticated HTTP proxies
- **Statistics:** Real-time tracking of checks, results, timing

State persists to `shopify_config.json` between runs.

### Site Rotation Strategy

- Sites used maximum 3 times before rotation
- Sites marked unavailable after consistent failures
- Permanent banning for sites requiring CAPTCHA or returning persistent errors
- Up to 5 site attempts per card before failure

### Proxy Configuration

Proxies use format: `host:port:username:password`
- PureVPN residential proxies via `pointtoserver.com`
- HTTP proxy authentication
- Dead proxy tracking and removal

### Output Categories

Results written to separate files:
- `charged.txt` - Successfully charged cards
- `live.txt` - Valid/approved cards
- `declined.txt` - Declined cards
- `challenge.txt` - 3D Secure/CAPTCHA required
- `suspicious.txt` - Unusual responses
- `unknown.txt` - Unclassified responses

### Known Issues

- Unicode encoding error when writing emoji characters to files on Windows (cp1252 codec)
- Proxy authentication failures (407 errors) with some proxy configurations
- Some sites require CAPTCHA which causes permanent banning

## External Dependencies

### Python Packages
- `python-telegram-bot` (v20.7) - Telegram bot framework for remote control
- `httpx` (v0.27.0) - Async HTTP client for Shopify API requests
- `aiofiles` (v23.2.1) - Async file operations for result logging
- `fake-useragent` (v1.4.0) - Random user agent generation for request spoofing
- `beautifulsoup4` (v4.12.3) - HTML parsing for checkout page scraping
- `python-dotenv` (v1.0.0) - Environment variable management

### External Services
- **Shopify Stores** - Target e-commerce sites for checkout processing
- **Shopify GraphQL API** - Payment processing and checkout completion
- **PureVPN Proxy Service** - Residential proxies via `pointtoserver.com:10780`
- **Telegram Bot API** - Remote command interface

### Configuration Files
- `shopify_config.json` - Persisted site lists, proxy configurations, banned sites
- `sites.txt` - Initial list of Shopify store URLs
- `cc_complete.txt` - Input file for mass card checking (user-provided)