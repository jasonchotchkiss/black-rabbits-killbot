# Black Rabbits Killbot — Session Notes
_Last updated: 2026-02-20 (Session 3)_

## My AI assistant name
Comet (at perplexity.ai)

## GitHub repo
https://github.com/jasonchotchkiss/black-rabbits-killbot (PRIVATE)

## Server: ubuntu-dev
- User: devuser
- Dev tree: ~/dev/black-rabbits-killbot (active dev, commits, pushes)
- Prod tree: /opt/black-rabbits-killbot (NOT YET CREATED)

## Env files (all gitignored)
- .env.dev — exists, has dev credentials
- .env.prod — exists but EMPTY, needs prod credentials filled in
- .env.example — template, committed to repo

## Deployment
- systemd service: br-killbot — NOT YET CREATED
- Service will point to /opt tree, use .env.prod

## Project architecture
- bot.py — Discord bot entry point, scheduler (4-hour sync, 11:15 UTC post)
- commands.py — All slash commands (/ping, /top10, /info, /killsagainst)
- stats.py — All database query functions
- database.py — DB init, save, helpers, lookup table upserts
- zkillboard.py — zKillboard + ESI API calls, kill data extraction
- sync.py — Kill sync runner (used by scheduler and direct run)
- resolve_names.py — One-time/repeatable backfill: corp/alliance IDs -> names

## Database: killboard.db (SQLite, gitignored)
Tables:
- kills — ~2,688 kills (pod kills already purged)
- corporations — 688 corps resolved from ESI
- alliances — EMPTY (see known issues below)

## Current working features (dev, confirmed in Discord)
- /ping — Online check
- /info — Bot info embed
- /top10 — Top 10 pilots by final blows (YTD, Month, Week)
- /killsagainst <target> — Autocomplete working for corps and characters
  - Autocomplete dropdown shows Pilot / Corp / Alliance suggestions as user types
  - Corp selection returns correct kill results ✅
  - Character selection returns correct kill results ✅
  - Alliance selection: autocomplete empty (see known issues)
- Pod kill filter — Capsule ship_type_ids 670 and 33328 excluded at API layer
- victim_alliance_id column exists in kills table
- 4-hour background kill sync (03:00, 07:00, 11:00, 15:00, 19:00, 23:00 UTC)
- 11:15 UTC daily auto-post to #br-top-killers
- After each sync: resolve_names.py runs automatically for new corp/alliance IDs

## Known issues / cosmetic bugs
1. /killsagainst embed title shows raw encoded value instead of friendly name
   Example: "Kills Against — corp:98407286" instead of "Kills Against — KARNAGE"
   Fix needed in commands.py (decode corp/alliance name for display)

2. alliances table is empty — all existing 2,688 kills have victim_alliance_id = 0
   because the column was added via ALTER TABLE after data was already loaded
   Fix: re-backfill existing kills from ESI to populate victim_alliance_id,
   then run resolve_names.py to populate alliances table

## Pending steps in order

### A — Cosmetic fix (quick, do first)
1. Fix commands.py: decode corp/alliance ID to name for embed title and entity_label
   - For corp: query corporations table for corp_name where corp_id = id
   - For ally: query alliances table for alliance_name where alliance_id = id
   - Add get_corporation_name(corp_id) and get_alliance_name(alliance_id) helpers to database.py

### B — Alliance backfill (bigger job)
2. Write a one-time re-backfill script (or extend resolve_names.py) that:
   - Reads all kill_ids from kills where victim_alliance_id = 0
   - Re-fetches ESI killmail for each using kill_id + zkb hash
     (need to store zkb_hash in kills table — currently not stored, need to add column)
   - Alternative: store zkb_hash now, then re-fetch
   - OR: use ESI /characters/{id}/ to resolve alliance from victim name — less accurate
   - Best approach TBD at start of next session

### C — Production deployment (after all dev features confirmed)
3. Fill in .env.prod with production credentials
4. Clone repo to /opt:
   sudo git clone https://github.com/jasonchotchkiss/black-rabbits-killbot /opt/black-rabbits-killbot
   cd /opt/black-rabbits-killbot
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   Copy .env.prod into /opt/black-rabbits-killbot/.env.prod
5. Run resolve_names.py in /opt to populate corp/alliance tables in prod DB
6. Create systemd service br-killbot pointing to /opt, using .env.prod
7. Start service and verify with journalctl

## Session workflow reminder
- Always run: cat -n FILENAME.py before editing (gives line numbers)
- Always run: python -m py_compile FILENAME.py after editing (catches syntax errors)
- When making multiple edits to one file: work bottom-to-top (line numbers don't shift)
- When a file is too tangled: select all in VS Code, replace entire file contents
- Commit after every confirmed-working step, not at end of session
