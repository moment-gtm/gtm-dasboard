# MCP Servers — Market Reference

**Purpose:** Quick-reference catalog of widely used Model Context Protocol (MCP) servers and what each is for.
**Compiled:** 2026-10-14

> The MCP ecosystem has thousands of servers and grows daily — there is no single "complete" list.
> The authoritative registries are:
> - Official reference repo: <https://github.com/modelcontextprotocol/servers>
> - MCP Registry / docs: <https://modelcontextprotocol.io/examples.md>
> - Community index (awesome-mcp-servers): <https://glama.ai/mcp/servers>
>
> Note: `modelcontextprotocol/servers` now keeps only a few **reference** servers. Older ones
> (GitHub, Slack, Postgres, etc.) moved to vendor-maintained repos or the archive.

---

## 1. Official Reference Servers (maintained by the MCP project)

| Server | Usage |
|---|---|
| **Filesystem** | Read/write/search files in allowed local directories |
| **Fetch** | Fetch a URL and convert web content to markdown for the model |
| **Git** | Run git operations — read repo, diff, commit, branch |
| **Memory** | Persistent knowledge-graph memory across sessions |
| **Sequential Thinking** | Structured step-by-step reasoning/planning scaffold |
| **Time** | Current time and timezone conversions |
| **Everything** | Demo/test server exercising all MCP features (prompts, tools, resources) |

## 2. Developer / Code Tools

| Server | Usage |
|---|---|
| **GitHub** (`github/github-mcp-server`) | Issues, PRs, Actions logs, repo & code search |
| **GitLab** | Merge requests, pipelines, repo management |
| **Playwright** (Microsoft) | Drive a real browser for testing/automation/scraping |
| **Puppeteer** | Headless Chrome browser automation (archived ref) |
| **Sentry** | Pull error/issue details into context for debugging |
| **Docker** | Manage containers, images, compose stacks |
| **Kubernetes** | Inspect/manage clusters, pods, deployments |
| **Context7** | Fetch up-to-date, version-accurate library docs |

## 3. Databases & Data

| Server | Usage |
|---|---|
| **PostgreSQL** | Query schema, run read-only SQL |
| **SQLite** | Local SQLite file queries |
| **MySQL** | Query/manage MySQL databases |
| **MongoDB** | Document queries and collection operations |
| **Redis** | Key-value cache operations |
| **Snowflake / BigQuery** | Cloud data-warehouse querying and analytics |
| **Supabase** | Postgres + auth + storage backend management |

## 4. Search & Web

| Server | Usage |
|---|---|
| **Brave Search** | Privacy-focused web search |
| **Tavily** | Search optimized for LLM/agent retrieval |
| **Exa** | Semantic/neural web search |
| **Perplexity** | Search with answer synthesis |
| **Firecrawl** | Crawl and scrape whole sites into clean markdown |

## 5. Productivity, Docs & Communication

| Server | Usage |
|---|---|
| **Slack** | Read/post messages, manage channels |
| **Google Drive** | Search and read Drive files |
| **Google Maps** | Geocoding, directions, place lookups |
| **Notion** | Read/update pages and databases |
| **Linear** | Manage issues, projects, sprints |
| **Jira / Confluence** (Atlassian) | Tickets, boards, wiki pages |
| **Figma** | Pull design files/components into context |

## 6. Cloud & Infrastructure

| Server | Usage |
|---|---|
| **AWS** (various) | Manage/query AWS services (S3, Lambda, etc.) |
| **Cloudflare** | Workers, DNS, KV, R2 management |
| **Vercel / Netlify** | Deployments and project config |
| **Stripe** | Payments, customers, invoices, subscriptions |

---

## Connectors Available in the Claude Code Session

These first-party connectors were listed in the working environment. Each requires authorization
via claude.ai connector settings before use.

| Connector | Usage |
|---|---|
| **Microsoft 365** | Outlook mail, OneDrive, Teams, Office files |
| **Gmail** | Read/send email |
| **Google Calendar** | View/manage events and scheduling |
| **Google Drive** | Search and read Drive files |
| **Adobe Customer Journey Analytics** | Cross-channel customer journey analytics |
| **Adobe Experience Manager** | Content and digital asset management |
| **Adobe Journey Optimizer** | Orchestrate customer journeys / campaigns |
| **Adobe Workfront** | Work and project management |
| **Adobe Marketing Agent** | Marketing automation assistance |
| **Adobe for creativity** | Creative Cloud asset/creativity tools |
| **FactSet AI-Ready Data** | Financial market and company data |
| **Sentry** | Application error monitoring |

---

## Selected for this project (Step 1 — Executive summary, 2026-10-15)

Chosen from the list above against the Executive summary's sources (SRC-01/02/04/16, offering catalogue)
and its acceptance tests. Configured in `.mcp.json` (project scope) unless noted.

| Server | Status | Why |
|---|---|---|
| **Playwright** (`@playwright/mcp`) | Installed (`.mcp.json`; approve on next start) | Drive the running dashboard for UAT (AC-02) and accessibility checks (AC-07) |
| **DuckDB** (`mcp-server-motherduck`, read-only) | Installed (`.mcp.json` as `gtm-duckdb`) | SQL over the platform snapshot `backend/var/gtm_snapshot.duckdb` — inspect raw/conformed/marts, debug metrics, reconciliation (AC-01) |
| **Microsoft 365** (claude.ai connector) | Available, **needs authorisation via `/mcp`** | Production path for SRC-16 Entra ID (SSO/RLS groups) and SharePoint (interim targets template SRC-02, offering catalogue). Mocked in the prototype |
| Adobe Workfront / Journey Optimizer / Marketing Agent / AEM / CJA | Available, not needed yet | Offerings (Step 5) and Market signals (Step 7) |
| Salesforce (SRC-01, the main Exec source) | **No MCP available** | Use the Salesforce REST/Bulk API; mocked by `connectors/mock.py` + `/mock/salesforce/*` |
| Git, GitHub, Sentry, Context7 | Not installed | Git isn't installed on this machine; add once version control / error monitoring exist |

## Finding the Current Full List

- **MCP Registry / official docs:** <https://modelcontextprotocol.io/examples.md>
- **Reference repo:** <https://github.com/modelcontextprotocol/servers>
- **Community indexes:**
  - awesome-mcp-servers (wong2): <https://docsearch.algolia.com/mcp/docs/repo/wong2/awesome-mcp-servers>
  - Glama MCP directory: <https://glama.ai/mcp/servers>
  - mcpmarket.com: <https://mcpmarket.com/daily/top-mcp-server-list-may-31-2026>

## Sources

- <https://github.com/modelcontextprotocol/servers>
- <https://modelcontextprotocol.io/examples.md>
- <https://modelcontextprotocol.net/examples>
- <https://blog.mcpservers.org/posts/best-mcp-servers-2026>
- <https://scrimba.com/articles/best-mcp-servers-for-developers-2026/>
- <https://glama.ai/mcp/servers>
