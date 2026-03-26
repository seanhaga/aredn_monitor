# AREDN Monitor

Self-contained Python HTTP server that fetches AREDN Prometheus metrics (`/cgi-bin/metrics`) server-side and serves a dashboard UI.

## Run

```bash
python3 aredn_monitor.py --host 0.0.0.0 --port 8765
```

Open the printed URL (default is `http://localhost:8765`).

## Add nodes in the UI

Use “+ Add Node”, enter a hostname/IP for the AREDN node, and the dashboard will fetch `/cgi-bin/metrics` from that host.
