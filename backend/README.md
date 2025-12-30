## BullBear Backend (Python)

This folder contains the Python backend for the **Crypto Market State Machine** ([Notion spec](https://www.notion.so/dunion/Crypto-Market-State-Machine-2d871b69c5b7809c8e9bdf8f317b6a0b)).

---

## Quick Start

### 1. Setup environment variables

```bash
cd backend
cp env.example .env
```

Edit `.env` and add your API keys:

```
CMC_API_KEY=your_coinmarketcap_api_key
TAAPI_SECRET=your_taapi_secret
```

| Variable | Required | Where to get |
|----------|----------|--------------|
| `CMC_API_KEY` | Yes | [CoinMarketCap API](https://coinmarketcap.com/api/) |
| `TAAPI_SECRET` | Yes | [TAAPI.io](https://taapi.io/) |

### 2. Install dependencies

```bash
# Install Poetry (if not already installed)
uv tool install poetry

# Install project dependencies
cd backend
poetry install
```

### 3. Run the server

```bash
poetry run uvicorn bullbear_backend.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be running at: **http://localhost:8000**

---

## Test Locally

### Health check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{"ok": true, "service": "bullbear-backend"}
```

### Fetch BTC price

```bash
curl http://localhost:8000/api/data/btc_price
```

Expected response:
```json
{
  "ok": true,
  "data_type": "btc_price",
  "value": 94205.82,
  "provider": "coinmarketcap",
  "metadata": {"currency": "USD"}
}
```

### Fetch MA50 / MA200

```bash
curl http://localhost:8000/api/data/ma50
curl http://localhost:8000/api/data/ma200
```

### Fetch market caps

```bash
curl http://localhost:8000/api/data/total_market_cap
curl http://localhost:8000/api/data/stablecoin_market_cap
```

### Fetch all data at once

```bash
curl http://localhost:8000/api/data
```

### Interactive API docs (Swagger)

Open in browser: **http://localhost:8000/docs**

---

## Run with Docker

```bash
cd backend

# Make sure .env file exists with your API keys
cp env.example .env

# Build and run
docker compose up --build
```

Then test: `curl http://localhost:8000/api/health`

---

## API Reference

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/data/{data_type}` | Fetch single data type |
| `GET /api/data` | Fetch all data types |

**Supported data types:**

| Data Type | Provider | Description |
|-----------|----------|-------------|
| `btc_price` | CoinMarketCap | BTC price in USD |
| `total_market_cap` | CoinMarketCap | Total crypto market cap |
| `stablecoin_market_cap` | CoinMarketCap | Stablecoin total market cap |
| `ma50` | TAAPI | 50-day moving average |
| `ma200` | TAAPI | 200-day moving average |

---

## Architecture (3 Layers)

```
data/
├── fetcher.py                   # Layer 1: DataFetcher (user-facing)
├── types.py                     # DataType enum + DataResult
│
├── sources/                     # Layer 2: Dedicated sources per data type
│   ├── btc_price.py             # → CoinMarketCap
│   ├── total_market_cap.py      # → CoinMarketCap
│   ├── stablecoin_market_cap.py # → CoinMarketCap
│   └── ma.py                    # → TAAPI (MA50/MA200)
│
└── providers/                   # Layer 3: Third-party API integrations
    ├── coinmarketcap.py         # CoinMarketCap API
    └── taapi.py                 # TAAPI.io API
```

---

## Useful Commands

```bash
# Install dependencies
poetry install

# Run server (with hot reload)
poetry run uvicorn bullbear_backend.main:app --reload --port 8000

# Add a new dependency
poetry add <package_name>

# Update dependencies
poetry update

# Run with Docker
docker compose up --build

# Stop Docker
docker compose down
```
