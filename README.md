# Liquidity Monitor Dashboard (EGX)

**Arabic Interactive Dashboard for Liquidity Flow Analysis**

- **Owner / Author:** Mahmoud Abdrabbo  
- **Version:** 1.1.0  
- **Copyright:** © 2026 Mahmoud Abdrabbo. All rights reserved.

---

## Overview
This dashboard visualizes daily liquidity flows for EGX stocks using:
- Inflow / Outflow / Net liquidity
- Watchlist ranking by net liquidity
- Symbol-level details and historical view
- Arabic company name cleanup (OCR fixes) + ticker-based overrides

> **Disclaimer:** This application is for informational purposes only and does not constitute investment advice.

---

## Features
- **Market or Symbol Scope**: choose a ticker to focus on one symbol, or view the whole market.
- **Interactive Filters**: date range, last session, last 10 sessions, net direction filters.
- **Arabic Name Fixes**: normalization + common OCR fixes + overrides by ticker.
- **Green/Red visuals**: positive net = green, negative net = red.
- **Built-in Help/About/README**: accessible inside the dashboard.
- **Watermark**: charts include an IP watermark.

---

## Running Locally
1) Install dependencies:
```bash
pip install -r requirements.txt
