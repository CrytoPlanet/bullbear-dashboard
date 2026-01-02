export interface DataResult {
    data_type: string;
    value: number;
    provider: string;
    metadata?: Record<string, any>;
    timestamp?: string;
}

export interface ApiResponse {
    ok: boolean;
    data: Record<string, DataResult>;
}

export const DATA_LABELS: Record<string, string> = {
    btc_price: 'BTC Price',
    total_market_cap: 'Total Market Cap',
    stablecoin_market_cap: 'Stablecoin Market Cap',
    ma50: '50-Day Moving Average',
    ma200: '200-Day Moving Average',
};
