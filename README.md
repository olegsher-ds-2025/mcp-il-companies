# mcp-il-companies

Due diligence on Israeli companies, partnerships, nonprofits (עמותות) and public benefit companies — live from data.gov.il.

**בדיקת נאותות לחברות, שותפויות, עמותות וחל"צ בישראל**

An [MCP](https://modelcontextprotocol.io) server that lets Claude and other AI assistants query official Israeli
government open data in plain language. No API key, no scraping — every call goes to the public
[data.gov.il](https://data.gov.il) CKAN API and returns the source with each answer.

## Tools

| Tool | What it does |
|---|---|
| `find_entity` | Find companies / partnerships / nonprofits / PBCs by name (Hebrew or English) |
| `entity_profile` | Full registry profile + registry changes (charges), liquidation, nonprofit certificates |
| `due_diligence` | Red-flag screen with risk level: inactive, violator (מפרה), stale reports, liquidation, charges, missing ניהול תקין |
| `search_nonprofits` | Nonprofits by keyword, sector and city |
| `health` | Connectivity check |

## Try asking

- “Is company 515052702 active and filing its annual reports?”
- “Run due diligence on 'וסטמה בע"מ' before I sign a contract.”
- “Find active education nonprofits in Haifa with revenue data.”

## Install

```bash
pip install git+https://github.com/olegsher-ds-2025/mcp-il-companies
```

Claude Desktop / Claude Code (`.mcp.json`):

```json
{ "mcpServers": { "il-companies": { "command": "mcp-il-companies" } } }
```

Run over HTTP (for remote hosting):

```bash
MCP_TRANSPORT=http PORT=8000 mcp-il-companies   # → http://localhost:8000/mcp
```

Prefect Horizon entrypoint: `server.py:mcp`.

## Data sources

- Registrar of Companies — companies (ica_companies)
- Registrar of Companies — partnerships
- Registrar of Companies — changes / charges
- Fast-track voluntary liquidations
- Registrar of Amutot — nonprofits, PBCs, proper-management certificates, foreign-state donations

All data © the publishing Israeli government authority, via data.gov.il. This project is independent and not
affiliated with the Government of Israel. Registry data can lag; verify critical facts with the authority.

## Development

```bash
pip install -e ".[dev]"
pytest            # offline tests
pytest -m live    # hits data.gov.il
```

## Roadmap

- [ ] Join with government procurement & OpenBudget contracts per company
- [ ] Officers / directors (not in open data — investigate)
- [ ] Securities Authority (MAYA) filings for public companies
- [ ] Bulk screening of a supplier list (CSV in, risk table out)

## Related

Part of a family of Israeli public-data MCP servers by [Oleg Sher](https://linkedin.com/in/sheroleg):
mcp-il-companies · mcp-il-vehicles · mcp-il-health · mcp-il-professionals · mcp-cbs-places · mcp-mavat.

## License

MIT
