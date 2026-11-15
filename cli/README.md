# SilentShorts CLI

Clip long videos into vertical 9:16 shorts from the terminal. Zero
dependencies; talks to the same API the dashboard, the MCP server and the
webhooks use.

```bash
pip install silentshorts        # or: uvx silentshorts / pipx run silentshorts

export SILENTSHORTS_API_KEY=osk_...   # from your account page at drunktrader.dev

silentshorts process "https://youtube.com/watch?v=..." --wait
silentshorts clips <job_id>
silentshorts publish <job_id> 0 --platforms tiktok,youtube
silentshorts quota
```

Self-hosted instance? Point it at your own machine and skip the key:

```bash
export SILENTSHORTS_API_URL=http://localhost:8000
silentshorts process "https://youtube.com/watch?v=..." --wait
```

For pipelines, prefer the webhook to `--wait`: pass `--webhook` and
`--webhook-secret` and SilentShorts POSTs once (HMAC-signed,
`X-SilentShorts-Signature: sha256=<hex>`) when the job ends, with clip titles
and durable download links.

The hosted free tier is 20 minutes/month with a watermark; paid plans from
$12/month. The self-hosted edition is MIT and has no meter. Agent-native
version of the same surface: [drunktrader.dev/mcp](https://www.drunktrader.dev/mcp).
