const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type PriceBar = {
  id: number;
  ticker: string;
  timestamp: string;
  timeframe: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
  trade_count: number | null;
  vwap: number | null;
  source: string;
};

export type RawDocument = {
  id: number;
  source_type: string;
  source_name: string | null;
  url: string | null;
  title: string | null;
  published_at: string | null;
  created_at: string | null;
};

export type MarketEvent = {
  id: number;
  ticker: string;
  event_type: string;
  sentiment: string;
  speaker: string | null;
  quote: string | null;
  impact_score: number | null;
  confidence: number | null;
  event_time: string | null;
  created_at: string | null;
};

export type DashboardResponse = {
  ticker: string;
  company: {
    id: number | null;
    ticker: string;
    name: string;
    sector: string;
    exchange: string;
  };
  latest_price: PriceBar | null;
  price_bars: PriceBar[];
  raw_documents: RawDocument[];
  market_events: MarketEvent[];
  status: {
    price_bars_count: number;
    raw_documents_count: number;
    market_events_count: number;
  };
};

export async function fetchDashboard(ticker: string): Promise<DashboardResponse> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard/${ticker}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard: ${response.status}`);
  }

  return response.json();
}
