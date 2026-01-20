#!/bin/bash
# Test runner script for Code Dojo
# This script provides convenient commands for running different types of tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if dependencies are installed
check_dependencies() {
    print_info "Checking dependencies..."

    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Installing test dependencies..."
        pip install -r requirements-test.txt
    fi

    if ! command -v playwright &> /dev/null; then
        print_error "Playwright not found. Installing Playwright..."
        pip install playwright
        playwright install chromium
    fi
}

# Function to run unit tests
run_unit_tests() {
    print_info "Running unit tests..."
    pytest tests/test_*.py -m "not playwright" -v --tb=short
}

# Function to run unit tests with coverage
run_unit_tests_with_coverage() {
    print_info "Running unit tests with coverage..."
    pytest tests/test_*.py -m "not playwright" -v --cov=. --cov-report=html --cov-report=term
    print_info "Coverage report saved to htmlcov/index.html"
}

# Function to start Flask app for testing
start_test_app() {
    print_info "Starting Flask application for testing..."

    # Check if app is already running
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
        print_warning "Application already running on port 5000"
        return 0
    fi

    # Start Flask app in background
    export FLASK_ENV=testing
    python app.py &
    APP_PID=$!
    echo $APP_PID > .test_app.pid

    # Wait for app to start
    sleep 3

    # Check if app started successfully
    if ! lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
        print_error "Failed to start Flask application"
        return 1
    fi

    print_info "Flask application started (PID: $APP_PID)"
}

# Function to stop test app
stop_test_app() {
    if [ -f .test_app.pid ]; then
        APP_PID=$(cat .test_app.pid)
        print_info "Stopping Flask application (PID: $APP_PID)..."
        kill $APP_PID 2>/dev/null || true
        rm .test_app.pid
    fi
}

# Function to run Playwright tests
run_playwright_tests() {
    print_info "Running Playwright E2E tests..."

    # Start app if not running
    start_test_app

    # Run Playwright tests
    pytest tests/playwright/ -m playwright -v --headed --slowmo 100

    # Stop app
    stop_test_app
}

# Function to run Playwright tests (headless for CI)
run_playwright_tests_ci() {
    print_info "Running Playwright E2E tests (headless)..."

    # Start app if not running
    start_test_app

    # Run Playwright tests
    pytest tests/playwright/ -m playwright -v --screenshot=only-on-failure

    # Stop app
    stop_test_app
}

# Function to run all tests
run_all_tests() {
    print_info "Running all tests..."

    # Run unit tests
    run_unit_tests

    # Run Playwright tests
    run_playwright_tests_ci
}

# Function to run specific test file
run_specific_test() {
    local test_file=$1
    print_info "Running test file: $test_file"
    pytest "$test_file" -v
}

# Show usage
show_usage() {
    echo "Code Dojo Test Runner"
    echo ""
    echo "Usage: ./run_tests.sh [command]"
    echo ""
    echo "Commands:"
    echo "  unit              Run unit tests only"
    echo "  unit-cov          Run unit tests with coverage report"
    echo "  playwright        Run Playwright E2E tests (headed)"
    echo "  playwright-ci     Run Playwright E2E tests (headless)"
    echo "  all               Run all tests"
    echo "  check             Check test dependencies"
    echo "  start-app         Start Flask app for manual testing"
    echo "  stop-app          Stop Flask test app"
    echo "  file <path>       Run specific test file"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh unit"
    echo "  ./run_tests.sh playwright"
    echo "  ./run_tests.sh file tests/test_github_pr.py"
}

# Main script logic
case "${1:-}" in
    unit)
        check_dependencies
        run_unit_tests
        ;;
    unit-cov)
        check_dependencies
        run_unit_tests_with_coverage
        ;;
    playwright)
        check_dependencies
        run_playwright_tests
        ;;
    playwright-ci)
        check_dependencies
        run_playwright_tests_ci
        ;;
    all)
        check_dependencies
        run_all_tests
        ;;
    check)
        check_dependencies
        ;;
    start-app)
        start_test_app
        ;;
    stop-app)
        stop_test_app
        ;;
    file)
        if [ -z "${2:-}" ]; then
            print_error "Please specify a test file"
            exit 1
        fi
        check_dependencies
        run_specific_test "$2"
        ;;
    *)
        show_usage
        ;;
esac
