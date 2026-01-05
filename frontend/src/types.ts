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

export interface ValidationLayer {
    risk_thermometer: string;
    ath_drawdown: number;
    ath_price?: number | null;
    etf_accelerator: string;
    etf_net_flow: number | null;
    etf_aum: number | null;
    etf_flow_14d_sum?: number | null;
    etf_flow_pos_ratio?: number | null;
    etf_flow_recent_avg?: number | null;
    etf_flow_prev_avg?: number | null;
    etf_flow_trend?: 'up' | 'down' | 'flat' | null;
    etf_aum_trend?: 'up' | 'down' | 'flat' | null;
}

export interface StateResult {
    state: string;
    trend: string;
    funding: string;
    risk_level: string;
    confidence: number;
    validation: ValidationLayer;
    metadata?: Record<string, any>;
}

export interface StateApiResponse {
    ok: boolean;
    state: string;
    trend: string;
    funding: string;
    risk_level: string;
    confidence: number;
    validation: ValidationLayer;
    metadata?: Record<string, any>;
}

export const DATA_LABELS: Record<string, string> = {
    btc_price: 'BTC Price',
    total_market_cap: 'Total Market Cap',
    stablecoin_market_cap: 'Stablecoin Market Cap',
    ma50: '50-Day Moving Average',
    ma200: '200-Day Moving Average',
    etf_net_flow: 'ETF Net Flow',
    etf_aum: 'ETF AUM',
};

export const STATE_STYLES: Record<string, { color: string; bgColor: string }> = {
    '牛市进攻': { color: '#ffffff', bgColor: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)' },
    '牛市修复': { color: '#ffffff', bgColor: 'linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%)' },
    '熊市反弹': { color: '#ffffff', bgColor: 'linear-gradient(135deg, #feca57 0%, #ff9ff3 100%)' },
    '熊市消化': { color: '#ffffff', bgColor: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)' },
};

export const RISK_COLORS: Record<string, string> = {
    'HIGH': '🔴',
    'MEDIUM': '🟡',
    'LOW': '🟢',
};
