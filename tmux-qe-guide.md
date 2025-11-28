# 🧪 Tmux for Quality Engineers - Practical Workflow Guide

## Your Current Setup vs. Enhanced Setup

### Current `start.sh`
- Creates **1 tmux session** with **1 pane**
- Runs Claude Code in that single pane
- You manually split panes after attaching

### Enhanced `start-enhanced.sh`
- Creates **1 tmux session** with **3 panes** automatically
- Layout optimized for QE workflows:
  ```
  ┌─────────────────┬─────────────────┐
  │ Claude Code     │ Test Runner     │
  │ (AI coding)     │ (watch tests)   │
  ├─────────────────┴─────────────────┤
  │ Logs/Shell (monitor/scripts)      │
  └───────────────────────────────────┘
  ```

## Essential Tmux Commands (Real QE Scenarios)

### Scenario 1: Running Tests While Coding with Claude
**Initial state:** Claude Code is in pane 0

1. Switch to test pane: `Ctrl+b →` (right arrow)
2. Start test watch: `npm run test:watch` or `pytest --watch`
3. Go back to Claude: `Ctrl+b ←` (left arrow)
4. Watch tests run automatically as Claude makes changes

### Scenario 2: Monitoring Application Logs
**When debugging test failures:**

1. Bottom pane (logs): `Ctrl+b ↓` twice
2. Tail logs: `tail -f logs/app.log` or `docker logs -f container_name`
3. Split horizontally to monitor multiple logs: `Ctrl+b "`
4. In new pane: `tail -f logs/test.log`
5. Navigate: `Ctrl+b o` (cycle through panes)

### Scenario 3: Exploratory Testing Session
**You need terminal, browser dev tools simulation, and notes:**

1. From Claude pane: `Ctrl+b %` (split vertically)
2. New pane for curl/API testing: `curl -X POST http://localhost:3000/api/test`
3. `Ctrl+b "` (split horizontally in right side)
4. New bottom-right pane for notes: `vim test-notes.md`

### Scenario 4: Performance Testing
**Running load tests while monitoring:**

1. Top-right pane: `artillery run load-test.yml`
2. Bottom pane: `watch -n 1 'ps aux | grep node'`
3. Add another monitoring pane: `Ctrl+b "` then `htop`

## Common QE Pane Layouts

### Layout 1: TDD Workflow (London School)
```
┌──────────────┬──────────────┐
│ Test First   │ Implement    │
│ (write test) │ (make pass)  │
├──────────────┴──────────────┤
│ Test Runner (continuous)    │
└─────────────────────────────┘
```

**Commands:**
```bash
# Top-left: Write test
vim test/user.test.js

# Top-right: Implement
vim src/user.js

# Bottom: Auto-run tests
npm run test:watch
```

### Layout 2: API Testing
```
┌──────────────┬──────────────┐
│ Test Script  │ API Calls    │
│ (playwright) │ (curl/httpie)│
├──────────────┴──────────────┤
│ Server Logs                 │
└─────────────────────────────┘
```

### Layout 3: Multi-Service Testing
```
┌──────────────┬──────────────┐
│ Service A    │ Service B    │
│ logs         │ logs         │
├──────────────┼──────────────┤
│ Test Runner  │ Database     │
│              │ queries      │
└──────────────┴──────────────┘
```

**Setup:**
```bash
# Create session
tmux new -s microservices

# Split into 4 panes
tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v

# Send commands to each pane
tmux send-keys -t 0 'docker logs -f service-a' C-m
tmux send-keys -t 1 'docker logs -f service-b' C-m
tmux send-keys -t 2 'npm run test:integration' C-m
tmux send-keys -t 3 'pgcli -h localhost -U postgres' C-m
```

## Advanced Tmux for QE

### Creating Named Windows for Different Test Types
```bash
# Attach to session
tmux attach -t alpha

# Create window for unit tests
Ctrl+b c  # creates new window
tmux rename-window -t alpha:1 'unit-tests'

# Create window for integration tests
Ctrl+b c
tmux rename-window -t alpha:2 'integration'

# Create window for E2E tests
Ctrl+b c
tmux rename-window -t alpha:3 'e2e'

# Switch between windows
Ctrl+b 0  # Go to window 0 (Claude Code)
Ctrl+b 1  # Go to unit-tests window
Ctrl+b 2  # Go to integration window
Ctrl+b n  # Next window
Ctrl+b p  # Previous window
```

### Copy Mode for Log Analysis
**When you need to search through logs:**

1. Enter copy mode: `Ctrl+b [`
2. Search backward: `?` then type search term
3. Search forward: `/` then type search term
4. Navigate: `↑↓←→` or `Ctrl+u` (page up), `Ctrl+d` (page down)
5. Start selection: `Space`
6. Copy selection: `Enter`
7. Paste: `Ctrl+b ]`
8. Exit copy mode: `q`

### Synchronize Panes (Run Same Command in All Panes)
**Useful for multi-environment testing:**

```bash
# Enable synchronize
Ctrl+b : setw synchronize-panes on

# Now type once, runs in all panes:
npm run test:smoke

# Disable synchronize
Ctrl+b : setw synchronize-panes off
```

## QE-Specific Aliases (Add to ~/.bashrc)

```bash
# Quick tmux layouts
alias tmux-qe='tmux new-session \; split-window -h \; split-window -v \; select-pane -t 0'
alias tmux-tdd='tmux new-session -n "tdd" \; send-keys "npm run test:watch" C-m \; split-window -h \; send-keys "vim src/" C-m'

# Quick test commands
alias tw='npm run test:watch'
alias tc='npm run test:coverage'
alias tci='npm run test:integration'
alias te2e='npm run test:e2e'

# Log monitoring
alias logs-app='tail -f logs/app.log'
alias logs-test='tail -f logs/test.log'
alias logs-error='tail -f logs/error.log | grep -i error'
```

## Tmux Configuration for QE (~/.tmux.conf)

```bash
# Reload config
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Better split commands
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# Mouse support (useful for resizing)
set -g mouse on

# Vim-like pane navigation
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Increase scrollback buffer
set -g history-limit 50000

# Start windows and panes at 1, not 0
set -g base-index 1
setw -g pane-base-index 1

# Renumber windows when one is closed
set -g renumber-windows on

# Status bar customization
set -g status-style bg=colour235,fg=colour136
set -g status-left '#[fg=colour235,bg=colour136,bold] QE Session: #S '
set -g status-right '#[fg=colour233,bg=colour241,bold] %Y-%m-%d #[fg=colour233,bg=colour245,bold] %H:%M:%S '
```

## Real-World QE Workflow Example

### Debugging a Flaky Test with PACT Framework Approach

**Proactive:**
```bash
# Pane 0: Claude Code analyzing test
"Claude, analyze this flaky test and suggest improvements"

# Pane 1: Run test 10 times to reproduce
for i in {1..10}; do npm test -- flaky-test.spec.js; done

# Pane 2: Monitor system resources
watch -n 1 'ps aux | head -20'
```

**Autonomous:**
```bash
# Pane 1: Let test runner watch for issues
npm run test:watch -- --detectLeaks

# Pane 2: Automated log aggregation
while true; do grep -i "error\|warning\|timeout" logs/*.log >> flaky-analysis.log; sleep 5; done
```

**Collaborative:**
```bash
# Pane 0: Pair with Claude on fix
# Pane 1: Share screen with team (screen recording)
asciinema rec debugging-session.cast

# Pane 2: Document findings in real-time
vim test-analysis.md
```

**Targeted:**
```bash
# Pane 0: Focus on specific test file
vim test/flaky-test.spec.js

# Pane 1: Run only this test with verbose output
npm test -- flaky-test.spec.js --verbose --detectLeaks

# Pane 2: Check network latency (if API test)
ping -c 100 api.example.com | tee latency-check.log
```

## Tmux Session Management

### Save Session for Later
```bash
# Install tmux-resurrect
git clone https://github.com/tmux-plugins/tmux-resurrect ~/.tmux/plugins/tmux-resurrect

# In ~/.tmux.conf add:
run-shell ~/.tmux/plugins/tmux-resurrect/resurrect.tmux

# Save session: Ctrl+b Ctrl+s
# Restore session: Ctrl+b Ctrl+r
```

### List and Switch Sessions
```bash
# List all sessions
tmux ls

# Attach to specific session
tmux attach -t alpha

# Switch session while inside tmux
Ctrl+b s  # Shows list, use arrows to select

# Rename current session
Ctrl+b $  # then type new name
```

## Troubleshooting

### Problem: Panes too small
```bash
# Resize current pane
Ctrl+b :resize-pane -D 10  # Down 10 lines
Ctrl+b :resize-pane -U 10  # Up 10 lines
Ctrl+b :resize-pane -R 20  # Right 20 columns
Ctrl+b :resize-pane -L 20  # Left 20 columns

# Or use mouse (if enabled)
```

### Problem: Lost which pane is which
```bash
# Show pane numbers
Ctrl+b q

# Show pane titles
Ctrl+b ,  # Rename window
# Type descriptive name like "unit-tests"
```

### Problem: Too many panes, can't see
```bash
# Zoom current pane to full screen
Ctrl+b z

# Toggle back to see all panes
Ctrl+b z
```

### Problem: Want to copy from tmux to system clipboard
```bash
# On macOS: install reattach-to-user-namespace
brew install reattach-to-user-namespace

# In ~/.tmux.conf:
set -g default-command "reattach-to-user-namespace -l ${SHELL}"

# On Linux: use xclip
sudo apt-get install xclip

# Copy from tmux:
Ctrl+b [ # Enter copy mode
# Select text
# y to copy (if vim bindings enabled)
# Ctrl+b ] to paste
```

## Integration with Claude Code

### Workflow: TDD with Claude
```bash
# Session setup
tmux new -s tdd-session

# Pane 0: Claude Code
claude --dangerously-skip-permissions

# In Claude: "Let's practice TDD for a user authentication module"

# Pane 1 (Ctrl+b %): Test runner
npm run test:watch

# Pane 2 (Ctrl+b " on pane 1): Git status
watch -n 2 git status --short
```

### Workflow: Exploratory Testing with AgentDB
```bash
# Pane 0: Claude Code with AgentDB pattern storage
# "Store patterns from this exploratory session"

# Pane 1: Browser automation
playwright codegen http://localhost:3000

# Pane 2: Test notes and findings
vim exploratory-findings-$(date +%Y%m%d).md
```

## Quick Reference Card

```
╔═══════════════════════════════════════════════════════════╗
║              TMUX QE QUICK REFERENCE                      ║
╠═══════════════════════════════════════════════════════════╣
║ Session Management                                        ║
║   tmux new -s name      Create new session                ║
║   tmux attach -t name   Attach to session                 ║
║   Ctrl+b d              Detach from session               ║
║   tmux ls               List sessions                     ║
║   Ctrl+b s              Switch sessions                   ║
╠═══════════════════════════════════════════════════════════╣
║ Panes (Split Screen)                                      ║
║   Ctrl+b %              Split vertically (left|right)     ║
║   Ctrl+b "              Split horizontally (top/bottom)   ║
║   Ctrl+b arrow          Navigate between panes            ║
║   Ctrl+b z              Zoom pane (toggle fullscreen)     ║
║   Ctrl+b x              Kill current pane                 ║
║   Ctrl+b o              Cycle through panes               ║
╠═══════════════════════════════════════════════════════════╣
║ Windows (Tabs)                                            ║
║   Ctrl+b c              Create new window                 ║
║   Ctrl+b n              Next window                       ║
║   Ctrl+b p              Previous window                   ║
║   Ctrl+b 0-9            Switch to window number           ║
║   Ctrl+b ,              Rename current window             ║
╠═══════════════════════════════════════════════════════════╣
║ Copy Mode (Log Analysis)                                  ║
║   Ctrl+b [              Enter copy mode                   ║
║   Space                 Start selection                   ║
║   Enter                 Copy selection                    ║
║   Ctrl+b ]              Paste                             ║
║   q                     Exit copy mode                    ║
║   /pattern              Search forward                    ║
║   ?pattern              Search backward                   ║
╠═══════════════════════════════════════════════════════════╣
║ QE-Specific Tips                                          ║
║   • Keep test runner in watch mode                        ║
║   • Use bottom pane for logs with tail -f                 ║
║   • Zoom pane when pair programming                       ║
║   • Sync panes for multi-environment testing              ║
║   • Name windows by test type (unit/integration/e2e)      ║
╚═══════════════════════════════════════════════════════════╝
```

## Next Steps

1. **Try the enhanced start script:**
   ```bash
   chmod +x start-enhanced.sh
   ./start-enhanced.sh
   ```

2. **Customize your layout** by editing the script's pane setup section

3. **Add your common test commands** to pane initialization

4. **Practice the keybindings** - muscle memory takes ~1 week

5. **Share your workflow** with the Serbian Agentic Foundation community!

---

*Remember: Quality isn't tested in, it's built in. Tmux helps you maintain fast feedback loops across multiple concerns simultaneously - the PACT way.*
