# Black Rabbits Killbot — Session Notes

## GitHub repo
[https://github.com/jasonchotchkiss/black-rabbits-killbot](https://github.com/jasonchotchkiss/black-rabbits-killbot) (PRIVATE)

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

## Current working features (dev, confirmed in Discord)
- /top10 — Top 10 pilots by final blows (YTD, Month, Week)
- /ping — Online check
- /info — Bot info embed (updated to list /killsagainst)
- /killsagainst <target> — Top 10 BR pilots who killed a specific pilot, corp, or alliance (CODE DONE, NOT YET TESTED IN DEV)
- 4-hour background kill sync (03:00, 07:00, 11:00, 15:00, 19:00, 23:00 UTC)
- 11:15 UTC daily auto-post to #br-top-killers
- DB has ~3,967 kills from backfill (includes pod kills — purge still needed, see below)

## Pod kill filter — fully done in code
- zkillboard.py: CAPSULE_TYPE_IDS = {670, 33328} done
- zkillboard.py: extract_kill_data() returns None for capsule ship types done
- zkillboard.py: victim_alliance_id added to return dict done
- database.py: victim_alliance_id INTEGER DEFAULT 0 column in CREATE TABLE done
- database.py: ALTER TABLE migration block in init_db() done
- database.py: victim_alliance_id included in save_kill() INSERT done

## /killsagainst — fully done in code
- stats.py: get_kills_against_character(), get_kills_against_corp(), get_kills_against_alliance() done
- stats.py: _query_kills_against() shared helper done
- commands.py: /killsagainst slash command done
- zkillboard.py: resolve_entity_name() calls ESI /universe/ids/ to auto-detect character/corp/alliance done
- Logic: exact ESI name match -> routes to correct query; fallback is fuzzy LIKE search on victim_name
- Note: ESI /universe/ids/ requires exact name — partial names fall back to character name search

## Pending steps in order
1. On ubuntu-dev, pull the latest code:
   git -C ~/dev/black-rabbits-killbot pull

2. Restart the bot so init_db() runs the migration (adds victim_alliance_id column):
   Kill and restart however you run it in dev (python bot.py or your dev runner)
   You should see: "Migration applied: added victim_alliance_id column."

3. Purge pod kills from the dev DB:
   sqlite3 ~/dev/black-rabbits-killbot/killboard.db "DELETE FROM kills WHERE ship_type_id IN (670, 33328);"
   Verify: sqlite3 ~/dev/black-rabbits-killbot/killboard.db "SELECT COUNT(*) FROM kills;"

4. Sync new tree in Discord (to register /killsagainst):
   The bot calls bot.tree.sync() on startup — just restarting registers the new command
   May take a few minutes to appear in Discord

5. Test in Discord:
   /killsagainst <exact character name>  — should resolve via ESI and return results
   /killsagainst <exact alliance name>   — should resolve via ESI and return results
   /killsagainst <partial/unknown name>  — should fall back to fuzzy character name search

6. Fill in .env.prod with production credentials

7. Clone repo to /opt:
   sudo git clone https://github.com/jasonchotchkiss/black-rabbits-killbot /opt/black-rabbits-killbot
   cd /opt/black-rabbits-killbot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   Copy .env.prod into /opt/black-rabbits-killbot/.env.prod
   Run backfill manually once to populate prod DB

8. Create systemd service pointing to /opt, using .env.prod

9. Start service and verify
