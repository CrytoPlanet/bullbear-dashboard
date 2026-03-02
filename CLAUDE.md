# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BullBear Dashboard is a crypto market state machine that classifies BTC's current market regime into one of four quadrants based on two inputs:
- **Trend** (MA50/MA200 with slope): Bullish or Bearish
- **Funding** (stablecoin vs total market cap dynamics): Offensive or Defensive

The result is one of four states: 牛市进攻 / 牛市修复 / 熊市反弹 / 熊市消化, plus a validation layer (ATH drawdown risk thermometer + ETF accelerator).

## Architecture

The project has two parts: a Python FastAPI backend and a Vue 3 TypeScript frontend, deployed as a static site on GitHub Pages.

### Backend (`backend/`)

Uses **Poetry** for dependency management. Python 3.12+ required.

**Layer structure:**
- `bullbear_backend/main.py` — FastAPI app with endpoints: `GET /api/health`, `GET /api/data/{data_type}`, `GET /api/data`, `GET /api/state`
- `bullbear_backend/data/fetcher.py` — `DataFetcher` class (main entry point); routes `DataType` enum values to source classes; has a 5-minute class-level cache
- `bullbear_backend/data/sources/` — One source class per `DataType`; each `fetch()` returns a `DataResult`
- `bullbear_backend/data/providers/` — Raw API clients: `BinanceProvider`, `CoinGeckoProvider`, `CoinMarketCapProvider`, `FarsideProvider`, `TaapiProvider`; use `get_provider(name)` factory
- `bullbear_backend/state_machine/engine.py` — `StateMachineEngine.evaluate()` fetches all data, runs trend + funding logic, returns `StateResult`
- `bullbear_backend/state_machine/types.py` — Enums/dataclasses: `TrendDirection`, `FundingBehavior`, `MarketState`, `StateResult`, `ValidationLayer`

**Data flow for `/api/state`:**
1. `StateMachineEngine` fetches BTC price, MA50, MA200, total/stablecoin market cap via `DataFetcher`
2. Gets 220-candle kline history from Binance + 30-day market cap history from CoinGecko
3. Computes MA slopes via log-scale linear regression
4. Determines trend (price vs MA200, MA200 slope) and funding (stablecoin/total cap slopes → 4 patterns)
5. Fetches ETF flow data from Farside Investors
6. Returns `StateResult` with state, trend, funding, risk level, confidence, and validation layer

### Frontend (`frontend/`)

Vue 3 with TypeScript, Vite, no component library. Single-file-component app — all logic lives in `src/App.vue`. No view routing (router is registered but has no routes).

**Data loading strategy:**
- In development (`localhost`): calls the FastAPI backend at `http://localhost:8000`
- In production (GitHub Pages): reads pre-generated static JSON files from GitHub Releases (`all_data.json`, `state.json`), falling back to `public/data/`

**Key files:**
- `src/types.ts` — All TypeScript interfaces (`DataResult`, `StateApiResponse`, `ValidationLayer`) and display constants (`STATE_STYLES`, `RISK_COLORS`, `DATA_LABELS`)
- `src/components/TradingViewChart.vue` — Embeds a TradingView BTC chart widget
- `vite.config.ts` — Sets `base` path to `/{repo-name}/` for GitHub Pages using `GITHUB_REPOSITORY` env var

### Static Data Generation

`backend/scripts/fetch_and_save_data.py` — Run by the `fetch-data.yml` GitHub Actions workflow on a schedule. Calls `DataFetcher` and `StateMachineEngine`, writes JSON output to `frontend/public/data/`. The deploy workflow triggers after this completes.

## Commands

### Backend

```bash
cd backend

# Install dependencies
poetry install

# Run dev server
poetry run uvicorn bullbear_backend.main:app --reload --host 0.0.0.0 --port 8000

# Lint
poetry run ruff check .
poetry run ruff format .

# Run tests (no tests exist yet)
poetry run pytest

# Generate static data files
poetry run python scripts/fetch_and_save_data.py

# Docker
docker compose up --build
```

### Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Run dev server (requires backend running at :8000)
pnpm dev

# Type check
pnpm type-check

# Build for production
pnpm build
```

## Configuration

Copy `backend/env.example` to `backend/.env`. Both API keys are optional — the default providers (Binance + CoinGecko + Farside) are all free and keyless:

```
CMC_API_KEY=...   # Optional: replaces CoinGecko for market cap data
TAAPI_SECRET=...  # Optional: replaces Binance for MA calculation
```

## CI/CD

- `fetch-data.yml` — Scheduled workflow; runs `scripts/fetch_and_save_data.py` and uploads `all_data.json` + `state.json` as a GitHub Release asset tagged `data`
- `deploy-pages.yml` — Builds the frontend and deploys to GitHub Pages; triggers on push to `main` or after `fetch-data.yml` succeeds

The frontend reads market data from the GitHub Release download URL: `https://github.com/CrytoPlanet/bullbear-dashboard/releases/download/data/all_data.json`.

## Adding a New Data Type

1. Add entry to `DataType` enum in `backend/bullbear_backend/data/types.py`
2. Create a source class in `backend/bullbear_backend/data/sources/` implementing `fetch() -> DataResult`
3. Wire it in `DataFetcher._get_source()` in `fetcher.py`
4. Add the type string to `DATA_TYPES` array in `frontend/src/App.vue`
5. Add a display label to `DATA_LABELS` in `frontend/src/types.ts`
