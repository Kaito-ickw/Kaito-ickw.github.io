# Waka-DS.com

**System Architecture & Data Strategy** — Technical blog by an IT Consultant specializing in data engineering, AI agent development, and SaaS optimization.

Built with [Jekyll](https://jekyllrb.com/) + [YAT theme](https://github.com/jeffreytse/jekyll-theme-yat). Deployed via GitHub Pages at [waka-ds.com](https://waka-ds.com).

---

## About

This repository is the source of [waka-ds.com](https://waka-ds.com) — a portfolio and knowledge base documenting production-tested solutions across:

- **Data Engineering**: ETL pipelines, SQL Server, Python (pandas, SQLAlchemy)
- **AI Agent Development**: LLM API integration (OpenAI, Anthropic), automated reasoning pipelines
- **Infrastructure**: Docker, WSL2, GitHub Actions, environment containerization
- **SaaS & DX Consulting**: Tech stack auditing, integration architecture, stakeholder alignment

> Building in production. Documenting what survives contact with reality.

---

## Tech Stack

| Layer | Stack |
|---|---|
| Languages | Python · TypeScript · SQL · Bash |
| Infrastructure | Docker · WSL2 · Linux (Ubuntu) |
| Data | SQL Server · pandas · SQLAlchemy |
| AI / LLM | OpenAI API · Anthropic Claude |
| Site | Jekyll · GitHub Pages · GitHub Actions |

---

## Development

Runs locally via Docker. No local Ruby/Jekyll installation required.

```bash
# Start dev server (http://localhost:4000)
docker compose up

# Stop
docker compose down

# Restart after _config.yml changes
docker compose restart jekyll
```

> **Note:** Changes to `_config.yml` require a container restart. SCSS, HTML, and Markdown changes are hot-reloaded automatically via `--livereload`.

---

## Contact

- X (Twitter): [@waka_ds_tech](https://x.com/waka_ds_tech)
- Blog: [waka-ds.com](https://waka-ds.com)

---

## License

Blog content: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Theme: [jekyll-theme-yat](https://github.com/jeffreytse/jekyll-theme-yat) by Jeffrey Tse (MIT License)
