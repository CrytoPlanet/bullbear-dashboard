## BullBear Backend (Python)

This folder contains the Python backend for the **Crypto Market State Machine** ([Notion spec](https://www.notion.so/dunion/Crypto-Market-State-Machine-2d871b69c5b7809c8e9bdf8f317b6a0b)).

---

### Architecture (3 Layers)

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

### Environment Variables

Copy `env.example` to `.env` and fill in your API keys:

```bash
cp env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `CMC_API_KEY` | Yes | CoinMarketCap API key ([get one](https://coinmarketcap.com/api/)) |
| `TAAPI_SECRET` | Yes | TAAPI.io secret ([get one](https://taapi.io/)) |

---

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/data/{data_type}` | Fetch single data type |
| `GET /api/data` | Fetch all data types |

**Supported data types:**
- `btc_price` — BTC price in USD (CoinMarketCap)
- `total_market_cap` — Total crypto market cap (CoinMarketCap)
- `stablecoin_market_cap` — Stablecoin total market cap (CoinMarketCap)
- `ma50` — 50-day moving average (TAAPI)
- `ma200` — 200-day moving average (TAAPI)

**Example:**
```bash
curl http://localhost:8000/api/data/btc_price
```

---

### Local Dev (Poetry)

Prerequisites:
- Python 3.12+
- Poetry (install via `uv`)

```bash
# Install Poetry with uv
uv tool install poetry

# Install dependencies
cd backend
poetry install

# Run the server
poetry run uvicorn bullbear_backend.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Docker

```bash
cd backend
docker compose up --build
```

Then open: `http://localhost:8000/api/health`
