#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 Agentists QuickStart - Enhanced Multi-Pane QE Launcher
# ═══════════════════════════════════════════════════════════════════════════════
# Enhanced version with 3-pane tmux layout for Quality Engineering workflows
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Phonetic alphabet for tmux sessions
PHONETIC_NAMES=("alpha" "bravo" "charlie" "delta" "echo" "foxtrot" "golf" "hotel" "india" "juliet" "kilo" "lima" "mike" "november" "oscar" "papa" "quebec" "romeo" "sierra" "tango" "uniform" "victor" "whiskey" "xray" "yankee" "zulu")

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_header() {
    local header=$1
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${BOLD}${header}${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to print error messages and exit
error_exit() {
    local message=$1
    print_message "$RED" "❌ ERROR: $message"
    echo ""
    print_message "$YELLOW" "💡 Troubleshooting tips:"
    echo "   1. Ensure all required tools are installed by running: .devcontainer/install-tools.sh"
    echo "   2. Check the installation report: cat .devcontainer/installation-report.md"
    echo "   3. Verify Node.js and npm are available: node --version && npm --version"
    echo "   4. For tmux issues, try: sudo apt-get install tmux"
    echo ""
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to find next available tmux session name
find_tmux_session() {
    for name in "${PHONETIC_NAMES[@]}"; do
        if ! tmux has-session -t "$name" 2>/dev/null; then
            echo "$name"
            return 0
        fi
    done
    # If all phonetic names are taken, use a timestamp
    echo "session-$(date +%s)"
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCRIPT START
# ═══════════════════════════════════════════════════════════════════════════════

print_header "🚀 Agentists QuickStart - Enhanced Multi-Pane QE Launcher"

# Step 1: Check prerequisites
print_message "$BLUE" "📋 Checking prerequisites..."

# Check for Node.js
if ! command_exists node; then
    error_exit "Node.js is not installed. Please install Node.js first."
fi

# Check for npm
if ! command_exists npm; then
    error_exit "npm is not installed. Please install npm first."
fi

# Check for tmux
if ! command_exists tmux; then
    print_message "$YELLOW" "⚠️  tmux is not installed. Attempting to install..."
    
    if command_exists apt-get; then
        if sudo apt-get install -y tmux >/dev/null 2>&1; then
            print_message "$GREEN" "✅ tmux installed successfully"
        else
            error_exit "Failed to install tmux. Please install it manually: sudo apt-get install tmux"
        fi
    else
        error_exit "tmux is not installed and automatic installation is not available on this system."
    fi
fi

# Check for claude command (Claude Code)
if ! command_exists claude; then
    print_message "$YELLOW" "⚠️  Claude Code is not installed. Attempting to install..."
    
    if npm install -g @anthropic-ai/claude-code 2>/dev/null || sudo npm install -g @anthropic-ai/claude-code 2>/dev/null; then
        print_message "$GREEN" "✅ Claude Code installed successfully"
    else
        error_exit "Failed to install Claude Code. Please install it manually: npm install -g @anthropic-ai/claude-code"
    fi
fi

# Check for claude-flow
if ! command_exists claude-flow; then
    print_message "$YELLOW" "⚠️  claude-flow is not installed. Attempting to install..."
    
    if npm install -g claude-flow@alpha 2>/dev/null || sudo npm install -g claude-flow@alpha 2>/dev/null; then
        print_message "$GREEN" "✅ claude-flow installed successfully"
    else
        error_exit "Failed to install claude-flow. Please install it manually: npm install -g claude-flow@alpha"
    fi
fi

print_message "$GREEN" "✅ All prerequisites are installed"

# Step 2: Initialize claude-flow
print_header "🌊 Claude Flow Initialization"

print_message "$CYAN" "Would you like to force reinitialize claude-flow?"
print_message "$CYAN" "This will overwrite any existing configuration."
echo ""
echo "Options:"
echo "  [y/Y] - Initialize with --force (overwrites existing config)"
echo "  [n/N] - Initialize normally (preserves existing config)"
echo "  [s/S] - Skip initialization"
echo ""
read -p "Your choice [y/n/s]: " -n 1 -r
echo ""

INIT_SUCCESS=false

case "$REPLY" in
    [yY])
        print_message "$BLUE" "🔧 Initializing claude-flow with --force..."
        if claude-flow init --force 2>/dev/null; then
            print_message "$GREEN" "✅ claude-flow initialized successfully (forced)"
            INIT_SUCCESS=true
        else
            print_message "$YELLOW" "⚠️  claude-flow initialization failed. This may be okay if it's already configured."
        fi
        ;;
    [nN])
        print_message "$BLUE" "🔧 Initializing claude-flow..."
        if claude-flow init 2>/dev/null; then
            print_message "$GREEN" "✅ claude-flow initialized successfully"
            INIT_SUCCESS=true
        else
            print_message "$YELLOW" "⚠️  claude-flow initialization failed. This may be okay if it's already configured."
        fi
        ;;
    [sS])
        print_message "$YELLOW" "⏭️  Skipping claude-flow initialization"
        ;;
    *)
        print_message "$YELLOW" "⚠️  Invalid choice. Skipping initialization."
        ;;
esac

# Step 3: Check for .mcp.json configuration
print_header "📦 MCP Configuration Check"

MCP_CONFIG_PATH="${WORKSPACE_FOLDER:-$(pwd)}/.mcp.json"
MCP_CONFIG_EXISTS=false

if [ -f "$MCP_CONFIG_PATH" ]; then
    print_message "$GREEN" "✅ Found .mcp.json configuration at: $MCP_CONFIG_PATH"
    MCP_CONFIG_EXISTS=true
else
    print_message "$YELLOW" "⚠️  No .mcp.json configuration found at: $MCP_CONFIG_PATH"
    print_message "$BLUE" "💡 Claude Code will run without MCP configuration"
fi

# Step 4: Create tmux session
print_header "🖥️  Tmux Multi-Pane Session Management"

# Find available session name
SESSION_NAME=$(find_tmux_session)
print_message "$BLUE" "🔍 Selected tmux session name: ${BOLD}$SESSION_NAME${NC}"

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    print_message "$YELLOW" "⚠️  Session '$SESSION_NAME' already exists. Attaching to it..."
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

# Step 5: Launch Claude Code in multi-pane tmux layout
print_header "🚀 Launching Multi-Pane QE Workspace"

print_message "$BLUE" "📝 Creating tmux session with 3-pane layout: $SESSION_NAME"
print_message "$CYAN" "   Layout: [Claude Code | Test Runner]"
print_message "$CYAN" "           [     Logs/Shell          ]"

# Prepare the Claude Code command
if [ "$MCP_CONFIG_EXISTS" = true ]; then
    CLAUDE_CMD="claude --dangerously-skip-permissions --mcp-config $MCP_CONFIG_PATH"
    print_message "$GREEN" "✅ Launching Claude Code with MCP configuration"
else
    CLAUDE_CMD="claude --dangerously-skip-permissions"
    print_message "$YELLOW" "⚠️  Launching Claude Code without MCP configuration"
fi

# Create tmux session with multi-pane layout
# Layout structure:
# ┌─────────────────┬─────────────────┐
# │                 │                 │
# │  Claude Code    │  Test Runner    │
# │  (Pane 0)       │  (Pane 1)       │
# │                 │                 │
# ├─────────────────┴─────────────────┤
# │                                   │
# │  Logs/Shell (Pane 2)              │
# │                                   │
# └───────────────────────────────────┘

if tmux new-session -d -s "$SESSION_NAME" 2>/dev/null; then
    
    # Pane 0: Run Claude Code (main pane, already exists)
    tmux send-keys -t "$SESSION_NAME:0.0" "$CLAUDE_CMD" C-m
    
    # Split vertically (create Pane 1 for test runner)
    tmux split-window -h -t "$SESSION_NAME:0"
    
    # Pane 1: Test runner / watcher area
    tmux send-keys -t "$SESSION_NAME:0.1" "# Test Runner Pane" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "# Ready for: npm test, npm run test:watch, pytest --watch, etc." C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo ''" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '💡 Common test commands:'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '   npm test              - Run tests once'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '   npm run test:watch    - Run tests in watch mode'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '   npm run test:coverage - Run with coverage'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '   pytest -v             - Run Python tests'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '   jest --watch          - Jest watch mode'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo ''" C-m
    
    # Split pane 1 horizontally (create Pane 2 for logs/shell)
    tmux split-window -v -t "$SESSION_NAME:0.1"
    
    # Pane 2: Logs and general shell
    tmux send-keys -t "$SESSION_NAME:0.2" "# Logs & Shell Pane" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "# Monitor logs: tail -f logs/*.log" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "# Watch files: watch -n 1 'command'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "# Run scripts: ./scripts/*.sh" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "echo ''" C-m
    
    # Select the Claude Code pane (pane 0) as the active one
    tmux select-pane -t "$SESSION_NAME:0.0"
    
    print_message "$GREEN" "✅ Multi-pane QE workspace created successfully!"
    echo ""
    print_header "📌 Session Information"
    
    echo -e "${GREEN}Multi-pane session created!${NC}"
    echo ""
    echo "🎯 Pane Layout:"
    echo "  • Pane 0 (top-left):    ${CYAN}Claude Code${NC} - Your AI pair programmer"
    echo "  • Pane 1 (top-right):   ${YELLOW}Test Runner${NC} - Run your test suites"
    echo "  • Pane 2 (bottom):      ${MAGENTA}Logs/Shell${NC} - Monitor logs, run scripts"
    echo ""
    echo "📋 Tmux Pane Commands Reference:"
    echo "  • Attach to session:        ${CYAN}tmux attach -t $SESSION_NAME${NC}"
    echo "  • Switch between panes:     ${CYAN}Ctrl+b, then arrow keys${NC}"
    echo "  • Zoom pane (full screen):  ${CYAN}Ctrl+b z${NC}"
    echo "  • Cycle through panes:      ${CYAN}Ctrl+b o${NC}"
    echo "  • Resize pane:              ${CYAN}Ctrl+b, hold Ctrl, arrow keys${NC}"
    echo "  • Kill current pane:        ${CYAN}Ctrl+b x${NC}"
    echo "  • Split pane horizontally:  ${CYAN}Ctrl+b \"${NC}"
    echo "  • Split pane vertically:    ${CYAN}Ctrl+b %${NC}"
    echo "  • Detach from session:      ${CYAN}Ctrl+b d${NC}"
    echo ""
    echo "🔧 Session Commands:"
    echo "  • List all sessions:        ${CYAN}tmux ls${NC}"
    echo "  • Kill this session:        ${CYAN}tmux kill-session -t $SESSION_NAME${NC}"
    echo "  • Rename session:           ${CYAN}tmux rename-session -t $SESSION_NAME newname${NC}"
    echo ""
    
    # Ask if user wants to attach immediately
    echo -e "${CYAN}Would you like to attach to the session now? [Y/n]: ${NC}"
    read -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_message "$BLUE" "🔗 Attaching to multi-pane session..."
        tmux attach-session -t "$SESSION_NAME"
    else
        print_message "$GREEN" "✨ Session is running in the background."
        print_message "$CYAN" "   To attach later, run: ${BOLD}tmux attach -t $SESSION_NAME${NC}"
    fi
else
    error_exit "Failed to create tmux session. Please check tmux installation and permissions."
fi

# Step 6: Success message
echo ""
print_header "✅ Setup Complete!"

print_message "$GREEN" "🎉 Your Multi-Pane QE Workspace is ready!"
echo ""
echo "🎯 Quick Start Guide:"
echo "  1. Attach to session: ${CYAN}tmux attach -t $SESSION_NAME${NC}"
echo "  2. Use ${CYAN}Ctrl+b${NC} then arrow keys to navigate panes"
echo "  3. Press ${CYAN}Ctrl+b z${NC} to zoom any pane to full screen"
echo "  4. Press ${CYAN}Ctrl+b d${NC} to detach (session keeps running)"
echo ""
echo "Resources:"
echo "  • Claude Flow Docs:  https://github.com/ruvnet/claude-flow"
echo "  • Claude Code Docs:  https://docs.anthropic.com/en/docs/claude-code"
echo "  • Tmux Cheatsheet:   https://tmuxcheatsheet.com/"
echo "  • Report Issues:     https://github.com/jedarden/agentists-quickstart/issues"
echo ""
print_message "$CYAN" "Happy testing! 🧪🚀"
