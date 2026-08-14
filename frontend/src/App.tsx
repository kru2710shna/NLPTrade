import { useEffect, useMemo, useState } from "react";
import "./styles.css";
import { fetchDashboard } from "./api/nlptrade";
import type { DashboardResponse } from "./api/nlptrade";

const UPCOMING = "Upcoming — we know what to fill and do next.";

function formatMoney(value: number | null | undefined) {
  if (value === null || value === undefined) return "Upcoming";
  return `$${value.toFixed(2)}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "Upcoming";

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

function formatVolume(value: number | null | undefined) {
  if (value === null || value === undefined) return "Upcoming";
  return new Intl.NumberFormat("en-US", { notation: "compact" }).format(value);
}

function App() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadDashboard() {
      try {
        setLoading(true);
        setErrorMessage(null);

        const data = await fetchDashboard("NVDA");

        if (mounted) {
          setDashboard(data);
        }
      } catch (error) {
        if (mounted) {
          setErrorMessage(error instanceof Error ? error.message : "Backend connection failed.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  const latestPrice = dashboard?.latest_price;

  const priceChange = useMemo(() => {
    const bars = dashboard?.price_bars ?? [];

    if (bars.length < 2) return null;

    const previous = bars[bars.length - 2];
    const latest = bars[bars.length - 1];

    const change = latest.close - previous.close;
    const changePct = (change / previous.close) * 100;

    return {
      change,
      changePct,
    };
  }, [dashboard]);

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">NTP</span>
          <strong>NLPTrade</strong>
          <span className="muted">/ TradeOnNews</span>
        </div>

        <nav className="nav" aria-label="Main navigation">
          <a href="#dashboard">Dashboard</a>
          <a href="#prices">Prices</a>
          <a href="#documents">Documents</a>
          <a href="#events">Events</a>
          <a href="#model">Model</a>
        </nav>

        <div className="status-pill">
          <span className="status-dot" />
          {loading ? "Connecting" : errorMessage ? "Backend issue" : "Backend connected"}
        </div>
      </header>

      <section className="ticker-strip">
        <span>TAPE</span>
        <span>NVDA · {formatMoney(latestPrice?.close)}</span>
        <span>Price bars · {dashboard?.status.price_bars_count ?? "Upcoming"}</span>
        <span>Documents · {dashboard?.status.raw_documents_count ?? "Upcoming"}</span>
        <span>Events · {dashboard?.status.market_events_count ?? "Upcoming"}</span>
      </section>

      <section className="hero" id="dashboard">
        <div>
          <p className="eyebrow">NLP-driven market intelligence</p>
          <h1>NLPTrade</h1>
          <p className="hero-copy">
            A backend-connected market intelligence shell for public signals,
            price reaction, raw evidence, event extraction, and future model outputs.
          </p>

          {errorMessage && (
            <p className="error-box">
              Backend connection failed: {errorMessage}. Make sure FastAPI is running on
              http://127.0.0.1:8000.
            </p>
          )}
        </div>

        <div className="hero-panel">
          <div className="panel-row">
            <span>Selected company</span>
            <strong>{dashboard?.company.name ?? "Upcoming"}</strong>
          </div>
          <div className="panel-row">
            <span>Ticker</span>
            <strong>{dashboard?.ticker ?? "NVDA"}</strong>
          </div>
          <div className="panel-row">
            <span>Latest close</span>
            <strong>{formatMoney(latestPrice?.close)}</strong>
          </div>
          <div className="panel-row">
            <span>Latest bar date</span>
            <strong>{formatDate(latestPrice?.timestamp)}</strong>
          </div>
        </div>
      </section>

      <section className="layout">
        <aside className="left-panel" id="documents">
          <div className="section-head">
            <span>Raw documents</span>
            <span className="muted">{dashboard?.status.raw_documents_count ?? 0}</span>
          </div>

          {dashboard?.raw_documents.length ? (
            dashboard.raw_documents.map((doc) => (
              <article className="feed-item" key={doc.id}>
                <div className="feed-title">
                  <strong>{doc.source_type}</strong>
                  <span>{formatDate(doc.published_at)}</span>
                </div>
                <p>{doc.title || UPCOMING}</p>
              </article>
            ))
          ) : (
            <article className="feed-item active">
              <div className="feed-title">
                <strong>Data not ingested yet</strong>
                <span>Upcoming</span>
              </div>
              <p>{UPCOMING}</p>
            </article>
          )}
        </aside>

        <section className="main-panel" id="prices">
          <div className="signal-header">
            <div>
              <p className="eyebrow">NVDA market data</p>
              <h2>{formatMoney(latestPrice?.close)}</h2>
              <p className="muted">
                {priceChange
                  ? `${priceChange.change >= 0 ? "+" : ""}${priceChange.change.toFixed(
                      2
                    )} (${priceChange.changePct.toFixed(2)}%) from previous bar`
                  : UPCOMING}
              </p>
            </div>

            <div className="credibility-box">
              <span>Data source</span>
              <strong>{latestPrice?.source ?? "Upcoming"}</strong>
            </div>
          </div>

          <blockquote>
            Price bars are now coming from the backend/Postgres. News, events, and model
            predictions will appear after ingestion and extraction.
          </blockquote>

          <div className="metric-grid">
            <section className="card">
              <div className="eyebrow">Open</div>
              <h3>{formatMoney(latestPrice?.open)}</h3>
              <p>Latest available daily bar.</p>
            </section>

            <section className="card">
              <div className="eyebrow">High</div>
              <h3>{formatMoney(latestPrice?.high)}</h3>
              <p>Latest available daily bar.</p>
            </section>

            <section className="card">
              <div className="eyebrow">Low</div>
              <h3>{formatMoney(latestPrice?.low)}</h3>
              <p>Latest available daily bar.</p>
            </section>

            <section className="card">
              <div className="eyebrow">Volume</div>
              <h3>{formatVolume(latestPrice?.volume)}</h3>
              <p>Latest available daily bar.</p>
            </section>
          </div>

          <section className="table-card">
            <div className="section-head">
              <span>Recent price bars</span>
              <span className="muted">Backend data</span>
            </div>

            {dashboard?.price_bars.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Open</th>
                      <th>High</th>
                      <th>Low</th>
                      <th>Close</th>
                      <th>Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.price_bars.slice(-10).reverse().map((bar) => (
                      <tr key={bar.id}>
                        <td>{formatDate(bar.timestamp)}</td>
                        <td>{formatMoney(bar.open)}</td>
                        <td>{formatMoney(bar.high)}</td>
                        <td>{formatMoney(bar.low)}</td>
                        <td>{formatMoney(bar.close)}</td>
                        <td>{formatVolume(bar.volume)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-chart">
                <span>{UPCOMING}</span>
              </div>
            )}
          </section>
        </section>

        <aside className="right-panel" id="events">
          <div className="section-head">
            <span>Market events</span>
            <span className="muted">{dashboard?.status.market_events_count ?? 0}</span>
          </div>

          {dashboard?.market_events.length ? (
            dashboard.market_events.map((event) => (
              <article className="feed-item" key={event.id}>
                <div className="feed-title">
                  <strong>{event.event_type}</strong>
                  <span>{event.sentiment}</span>
                </div>
                <p>{event.quote || event.speaker || UPCOMING}</p>
              </article>
            ))
          ) : (
            <article className="feed-item active">
              <div className="feed-title">
                <strong>Event extraction</strong>
                <span>Upcoming</span>
              </div>
              <p>{UPCOMING}</p>
            </article>
          )}

          <section className="source-card" id="model">
            <div className="section-head">
              <span>Model status</span>
            </div>

            <div className="source-row">
              <span>Sentiment</span>
              <strong>Upcoming</strong>
            </div>
            <div className="source-row">
              <span>Event labels</span>
              <strong>Upcoming</strong>
            </div>
            <div className="source-row">
              <span>Training set</span>
              <strong>Upcoming</strong>
            </div>
            <div className="source-row">
              <span>Prediction</span>
              <strong>Upcoming</strong>
            </div>
          </section>
        </aside>
      </section>

      <footer className="footer">
        <strong>Not financial advice.</strong> NLPTrade analyzes public,
        non-privileged information only. Model outputs will be statistical estimates, not
        trading recommendations.
      </footer>
    </main>
  );
}

export default App;
