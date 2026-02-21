# Working with Comet — Python Dev Workflow Guide

## Who is Comet?
Comet is the AI assistant at perplexity.ai. Each new conversation is a clean
session with no memory of previous sessions. This guide prevents context loss.

---

## STARTING A NEW SESSION (resuming a project)

1. Open a NEW Comet conversation at perplexity.ai (not the old thread)
2. Open GitHub in a browser tab and stay logged in:
   https://github.com/jasonchotchkiss/black-rabbits-killbot
3. Print your notes:
   cat ~/dev/black-rabbits-killbot/NOTES.md
4. Paste the full output as your very first message — no prefix needed.
   Comet will read it and pick up exactly where you left off.

---

## ENDING A SESSION CLEANLY

1. Update NOTES.md with current status (open in VS Code, select all, replace)
2. Commit everything:
   cd ~/dev/black-rabbits-killbot
   git add -A
   git commit -m "End of session: describe what was done"
   git push
   git status   # should say "nothing to commit, working tree clean"
3. Close the Comet tab — nothing else needed.

---

## FILE EDITING PROTOCOL (established Session 3)

### Before editing any file
Always get line numbers first:
   cat -n ~/dev/black-rabbits-killbot/FILENAME.py

### Making edits in VS Code
- Open file: code ~/dev/black-rabbits-killbot/FILENAME.py
- Save after every change: Ctrl+S
- When making multiple edits to the same file: work bottom-to-top
  (editing lower line numbers last prevents line number shifting)
- When a file is badly tangled: Ctrl+A to select all, delete, paste clean version

### After every edit
Always syntax-check before committing:
   python -m py_compile FILENAME.py
Silence = clean. Any output = error with line number shown.

### Committing
   git add FILENAME.py
   git commit -m "description of change"
   git push

---

## STARTING A NEW PROJECT

### Step 1 — Set up directory structure
Dev and prod trees are always kept separate:
   ~/dev/PROJECT_NAME/       <- active development
   /opt/PROJECT_NAME/        <- production (deployed from git, never edited directly)

### Step 2 — Initialize the project
   cd ~/dev
   mkdir PROJECT_NAME && cd PROJECT_NAME
   git init
   python3 -m venv .venv
   source .venv/bin/activate
   git remote add origin https://github.com/USERNAME/PROJECT_NAME.git

### Step 3 — Create NOTES.md immediately (before writing any code)
Always gitignored. This is your session handoff document.
   touch NOTES.md
   echo "NOTES.md" >> .gitignore
   echo "NEXT_SESSION.md" >> .gitignore

### Step 4 — Start Comet session by pasting NOTES.md as your first message

---

## IF CONTEXT GETS COMPRESSED MID-SESSION

Signs:
- Comet contradicts earlier decisions
- Comet forgets your directory structure or env file names
- Comet suggests creating things that already exist

Fix:
1. Stop and say: "Let's pause. Here is my current project state:"
   then paste NOTES.md
2. If rendering is also broken, end the session and start fresh
3. Never let Comet proceed with incorrect assumptions

---

## PRODUCTION DEPLOYMENT CHECKLIST

1. Clone to /opt (first time only):
   sudo git clone https://github.com/USERNAME/PROJECT_NAME.git /opt/PROJECT_NAME
   sudo chown -R devuser:devuser /opt/PROJECT_NAME
   cd /opt/PROJECT_NAME && python3 -m venv .venv
   source .venv/bin/activate && pip install -r requirements.txt

2. Copy env file (never via git):
   cp ~/dev/PROJECT_NAME/.env.prod /opt/PROJECT_NAME/.env.prod
   nano /opt/PROJECT_NAME/.env.prod   # fill in credentials

3. Pull updates to prod after that:
   cd /opt/PROJECT_NAME && git pull origin main

4. Create systemd service:
   sudo nano /etc/systemd/system/SERVICE_NAME.service

   Template:
   [Unit]
   Description=PROJECT_NAME
   After=network.target
   [Service]
   Type=simple
   User=devuser
   WorkingDirectory=/opt/PROJECT_NAME
   ExecStart=/opt/PROJECT_NAME/.venv/bin/python bot.py
   Restart=always
   RestartSec=10
   EnvironmentFile=/opt/PROJECT_NAME/.env.prod
   [Install]
   WantedBy=multi-user.target

5. Enable and start:
   sudo systemctl daemon-reload
   sudo systemctl enable SERVICE_NAME
   sudo systemctl start SERVICE_NAME
   sudo systemctl status SERVICE_NAME

6. Watch logs:
   sudo journalctl -u SERVICE_NAME -f

---

## QUICK REFERENCE

   source ~/dev/PROJECT_NAME/.venv/bin/activate    # activate venv
   cat -n FILENAME.py                              # view file with line numbers
   python -m py_compile FILENAME.py               # syntax check
   git add -A && git commit -m "msg" && git push  # commit and push
   sudo systemctl status SERVICE_NAME             # check prod service
   sudo systemctl restart SERVICE_NAME            # restart after git pull
   sudo journalctl -u SERVICE_NAME -f             # live logs
   cat ~/dev/black-rabbits-killbot/NOTES.md       # print session handoff