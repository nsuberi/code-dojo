#!/bin/bash
# Code Dojo Startup Script
# Ensures database is properly seeded before starting Flask

set -e  # Exit on error

# Colors for output (following run_tests.sh pattern)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PORT=5002
DB_PATH="instance/code_dojo.db"

# Helper functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Show usage
show_usage() {
    echo "Code Dojo Startup Script"
    echo ""
    echo "Usage: ./start.sh [command]"
    echo ""
    echo "Commands:"
    echo "  (none)        Drop all tables, reseed from scratch, start app"
    echo "  --fresh       Drop DB, reseed everything, start app (with confirmation)"
    echo "  --seed-only   Seed database but don't start app"
    echo "  --no-seed     Skip DB checks, just start app (quick restart)"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start.sh              # Normal startup"
    echo "  ./start.sh --fresh      # Reset everything"
    echo "  ./start.sh --no-seed    # Quick restart"
}

# Check Python environment
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3."
        exit 1
    fi
}

# Activate virtual environment if present
activate_venv() {
    if [ -d "venv" ]; then
        print_info "Activating virtual environment..."
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        print_info "Activating virtual environment..."
        source .venv/bin/activate
    else
        print_warning "No virtual environment found. Consider creating one:"
        print_warning "  python3 -m venv venv"
        print_warning "  source venv/bin/activate"
        print_warning "  pip install -r requirements.txt"
    fi
}

# Check if Flask is installed
check_dependencies() {
    if ! python3 -c "import flask" 2>/dev/null; then
        print_error "Flask not installed."
        read -p "Install dependencies now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pip install -r requirements.txt
        else
            print_error "Cannot start without Flask."
            exit 1
        fi
    fi
}

# Check if port is available
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $PORT is already in use."
        read -p "Kill existing process and restart? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill $(lsof -ti:$PORT) 2>/dev/null || true
            sleep 1
        else
            print_error "Cannot start - port $PORT is in use."
            exit 1
        fi
    fi
}

# Smart database seeding
seed_database() {
    print_info "Checking database health..."
    python3 seed_data.py --smart
}

# Reset database (destructive)
reset_database() {
    print_warning "This will DELETE all data and reset the database!"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Backup existing database
        if [ -f "$DB_PATH" ]; then
            BACKUP_FILE="${DB_PATH}.backup_$(date +%Y%m%d_%H%M%S)"
            print_info "Backing up database to $BACKUP_FILE"
            cp "$DB_PATH" "$BACKUP_FILE"
        fi

        print_info "Resetting database..."
        python3 seed_data.py --reset
        python3 seed_data.py --rubrics
        python3 seed_data.py --challenge-rubric
        print_success "Database reset complete"
    else
        print_info "Reset cancelled."
        exit 0
    fi
}

# Start Flask application
start_flask() {
    print_info "Starting Flask on port $PORT..."
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🚀 Code Dojo is ready!${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "   Open ${BLUE}http://localhost:$PORT${NC} in your browser"
    echo ""
    echo "   Demo Accounts:"
    echo "   - Admin:      admin@codedojo.com / admin123"
    echo "   - Instructor: instructor@codedojo.com / instructor123"
    echo "   - Student:    alice@example.com / student123"
    echo ""
    echo "   Press Ctrl+C to stop the server"
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""

    python3 app.py
}

# Cleanup on exit
cleanup() {
    echo ""
    print_info "Shutting down..."
}

trap cleanup EXIT

# Main script logic
case "${1:-}" in
    --help)
        show_usage
        exit 0
        ;;
    --fresh)
        check_python
        activate_venv
        check_dependencies
        reset_database
        check_port
        start_flask
        ;;
    --seed-only)
        check_python
        activate_venv
        check_dependencies
        seed_database
        print_success "Seeding complete (app not started)"
        ;;
    --no-seed)
        check_python
        activate_venv
        check_dependencies
        check_port
        print_info "Skipping database checks..."
        start_flask
        ;;
    "")
        # Default: drop all tables and reseed
        check_python
        activate_venv
        check_dependencies
        print_info "Dropping all tables and reseeding database..."
        python3 seed_data.py --reset
        python3 seed_data.py --rubrics
        python3 seed_data.py --challenge-rubric
        print_success "Database reset complete"
        check_port
        start_flask
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
