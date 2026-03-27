# AREDN Monitor

Self-contained Python HTTP server that fetches AREDN Prometheus metrics (`/cgi-bin/metrics`) server-side and serves a dashboard UI.

## Run

```bash
python3 aredn_monitor.py --host 0.0.0.0 --port 8765
```

Open the printed URL (default is `http://localhost:8765`).

## Optional Config File

You can provide `--config` to pre-load dashboard nodes and (optionally) set the server host/port.

```bash
python3 aredn_monitor.py --config config.json
```

Example schema (`config.example.json`):
- `server.host` / `server.port` (optional): defaults to `127.0.0.1:8765`
- `dashboard.refresh_seconds` (optional): one of `0, 15, 30, 60, 120` (defaults to `30`)
- `dashboard.nodes` (optional): array of `{ "host": "...", "name": "..." }`
- `storage.enabled` / `storage.directory` (optional): when `enabled` is true, each successful `/cgi-bin/metrics` fetch is appended as one JSON line to `<directory>/<node>.jsonl` (parsed metrics plus UTC timestamp). Use for local history or offline analysis; files can grow quickly if the refresh interval is short.

### Metrics storage (CLI)

Enable logging without editing config:

```bash
python3 aredn_monitor.py --storage ./metrics_data
```

This overrides `storage` in the config file if both are set.

## Add nodes in the UI

Use “+ Add Node”, enter a hostname/IP for the AREDN node, and the dashboard will fetch `/cgi-bin/metrics` from that host.
