#!/bin/bash

# ============================================================================
# E2E Testing Script
# ============================================================================
# Usage:
#   ./e2e_test.sh [options]
#
# Options:
#   --clean-db          Clean database before running tests
#   --debug             Enable debug mode (verbose output)
#   --flow=<name>       Run specific flow only (auth|settings|team|all)
#   --help              Show this help message
#
# Examples:
#   ./e2e_test.sh --clean-db --debug
#   ./e2e_test.sh --flow=auth
#   ./e2e_test.sh --clean-db --flow=settings
# ============================================================================

set -e

# Configuration
BASE_URL="http://localhost:8000"
API_VERSION="v1.0"
API_URL="$BASE_URL/$API_VERSION"
EMAIL="test.user@example.com"
CAMEL_EMAIL="Test.User@Example.com"

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TOTAL_ENDPOINTS=0
CURRENT_TEST=0

# Flags
CLEAN_DB=false
DEBUG=false
FLOW="all"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo ""
    echo "================================================================"
    echo "  $1"
    echo "================================================================"
}

print_step() {
    CURRENT_TEST=$((CURRENT_TEST + 1))
    echo ""
    echo -e "${BLUE}📝 TEST CASE #$CURRENT_TEST: $1${NC}"
}

print_endpoint() {
    TOTAL_ENDPOINTS=$((TOTAL_ENDPOINTS + 1))
    echo -e "${YELLOW}🔗 ENDPOINT #$TOTAL_ENDPOINTS: $1${NC}"
}

print_success() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}❌ $1${NC}"
}

print_debug() {
    if [ "$DEBUG" = true ]; then
        echo -e "${YELLOW}🔍 DEBUG: $1${NC}"
    fi
}

cleanup_temp_files() {
    rm -f tmp_*.json 2>/dev/null || true
}

check_response() {
    local response_code=$1
    local expected_code=$2
    local description=$3
    
    if [[ "$response_code" == "$expected_code" ]]; then
        print_success "$description (HTTP $response_code)"
        return 0
    else
        print_error "$description (Expected HTTP $expected_code, got $response_code)"
        if [ "$DEBUG" = true ] && [ -f "tmp_error_response.json" ]; then
            echo "Response body:"
            cat tmp_error_response.json
        fi
        exit 1
    fi
}

validate_json_field() {
    local file=$1
    local field=$2
    local expected=$3
    local description=$4
    
    local actual=$(jq -r "$field" "$file")
    
    if [[ "$actual" == "$expected" ]]; then
        print_success "$description: $actual"
        return 0
    else
        print_error "$description (Expected: $expected, Got: $actual)"
        exit 1
    fi
}

validate_json_not_null() {
    local file=$1
    local field=$2
    local description=$3
    
    local value=$(jq -r "$field" "$file")
    
    if [[ "$value" != "null" && -n "$value" ]]; then
        print_success "$description: $value"
        return 0
    else
        print_error "$description is null or empty"
        exit 1
    fi
}

# ============================================================================
# Database Cleanup
# ============================================================================

clean_database() {
    if [ "$CLEAN_DB" = true ]; then
        print_header "DATABASE CLEANUP"
        if [ -f "./db_cleanup.sh" ]; then
            echo "Running database cleanup script..."
            ./db_cleanup.sh
            print_success "Database cleaned successfully"
        else
            echo "⚠️  Warning: db_cleanup.sh not found, skipping cleanup"
        fi
    fi
}

# ============================================================================
# Test Flow: Server Health Check
# ============================================================================

test_server_health() {
    print_step "Server Health Check"
    print_endpoint "GET $BASE_URL/ping"
    
    response=$(curl -s -w "%{http_code}" -o tmp_ping_response.json "$BASE_URL/ping")
    
    check_response "$response" "200" "Server ping"
    validate_json_field "tmp_ping_response.json" ".status" "ok" "Status field"
    
    print_debug "Server is healthy and responding"
}

# ============================================================================
# Test Flow: Authentication
# ============================================================================

test_auth_flow() {
    print_header "AUTHENTICATION FLOW"
    
    # Step 1: Sign In
    print_step "Sign In Request"
    print_endpoint "POST $API_URL/signin"
    
    response=$(curl -s -w "%{http_code}" -o tmp_signin_response.json -X POST "$API_URL/signin" \
      -H "Content-Type: application/json" \
      -d "{\"email\": \"$EMAIL\"}")
    
    check_response "$response" "200" "Sign in request"
    validate_json_not_null "tmp_signin_response.json" ".token" "Magic token"
    
    TOKEN=$(jq -r '.token' tmp_signin_response.json)
    print_debug "Token: $TOKEN"
    
    sleep 1
    
    # Step 2: Confirm Sign In
    print_step "Confirm Sign In"
    print_endpoint "GET $API_URL/signin/confirm?token=$TOKEN"
    
    response=$(curl -s -w "%{http_code}" -o tmp_confirm_response.json \
      "$API_URL/signin/confirm?token=$TOKEN")
    
    check_response "$response" "200" "Sign in confirmation"
    validate_json_not_null "tmp_confirm_response.json" ".access_token" "Access token"
    
    ACCESS_TOKEN=$(jq -r '.access_token' tmp_confirm_response.json)
    print_debug "Access Token received"
    
    sleep 1
    
    # Step 3: Get Current User
    print_step "Get Current User"
    print_endpoint "GET $API_URL/me"
    
    response=$(curl -s -w "%{http_code}" -o tmp_me_response.json \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      "$API_URL/me")
    
    check_response "$response" "200" "Get current user"
    validate_json_not_null "tmp_me_response.json" ".id" "User ID"
    validate_json_not_null "tmp_me_response.json" ".email" "User email"
    
    ORIGINAL_USER_ID=$(jq -r '.id' tmp_me_response.json)
    ORIGINAL_USER_EMAIL=$(jq -r '.email' tmp_me_response.json)
    
    print_debug "User ID: $ORIGINAL_USER_ID"
    print_debug "User Email: $ORIGINAL_USER_EMAIL"
    
    sleep 1
    
    # Step 4: Check Welcome Notification
    print_step "Check Welcome Notification"
    print_endpoint "GET $API_URL/notifications"
    
    response=$(curl -s -w "%{http_code}" -o tmp_notifications.json \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      "$API_URL/notifications")
    
    check_response "$response" "200" "Fetch notifications"
    
    notif_count=$(jq 'length' tmp_notifications.json)
    if [[ "$notif_count" -gt 0 ]]; then
        print_success "Notifications found: $notif_count"
    else
        print_error "No notifications found"
        exit 1
    fi
    
    # Look for welcome notification
    welcome_notif=$(jq '.[] | select(.type=="signup_successful")' tmp_notifications.json)
    if [[ -n "$welcome_notif" ]]; then
        print_success "Welcome notification found"
    else
        print_error "Welcome notification not found"
        exit 1
    fi
    
    sleep 1
    
    # Step 5: Case-Insensitive Email Login
    print_step "Case-Insensitive Email Login"
    print_endpoint "POST $API_URL/signin (CamelCase email)"
    
    camel_response=$(curl -s -w "%{http_code}" -o tmp_camel_signin_response.json \
      -X POST "$API_URL/signin" \
      -H "Content-Type: application/json" \
      -d "{\"email\": \"$CAMEL_EMAIL\"}")
    
    check_response "$camel_response" "200" "CamelCase email sign in"
    
    camel_token=$(jq -r '.token' tmp_camel_signin_response.json)
    
    print_endpoint "GET $API_URL/signin/confirm?token=$camel_token"
    camel_confirm=$(curl -s -w "%{http_code}" -o tmp_camel_confirm.json \
      "$API_URL/signin/confirm?token=$camel_token")
    
    check_response "$camel_confirm" "200" "CamelCase email confirmation"
    
    camel_access_token=$(jq -r '.access_token' tmp_camel_confirm.json)
    
    print_endpoint "GET $API_URL/me"
    curl -s -H "Authorization: Bearer $camel_access_token" \
      "$API_URL/me" > tmp_camel_me.json
    
    camel_user_id=$(jq -r '.id' tmp_camel_me.json)
    camel_user_email=$(jq -r '.email' tmp_camel_me.json)
    
    if [[ "$camel_user_id" == "$ORIGINAL_USER_ID" && "$camel_user_email" == "$ORIGINAL_USER_EMAIL" ]]; then
        print_success "CamelCase login returns same user"
    else
        print_error "CamelCase login user mismatch"
        echo "Expected ID: $ORIGINAL_USER_ID / Got: $camel_user_id"
        echo "Expected Email: $ORIGINAL_USER_EMAIL / Got: $camel_user_email"
        exit 1
    fi
    
    # Export ACCESS_TOKEN for other flows
    export ACCESS_TOKEN
}

# ============================================================================
# Test Flow: Settings
# ============================================================================

test_settings_flow() {
    print_header "SETTINGS FLOW"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "ACCESS_TOKEN not set. Run auth flow first."
        exit 1
    fi
    
    # Step 1: Get Initial Settings
    print_step "Get Initial Settings"
    print_endpoint "GET $API_URL/settings"
    
    response=$(curl -s -w "%{http_code}" -o tmp_settings.json \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      "$API_URL/settings")
    
    check_response "$response" "200" "Fetch settings"
    
    # Validate general settings exist
    general_exists=$(jq '.general' tmp_settings.json)
    if [[ "$general_exists" != "null" ]]; then
        print_success "General settings section exists"
    else
        print_error "General settings section missing"
        exit 1
    fi
    
    sleep 1
    
    # Step 2: Update General Settings
    print_step "Update General Settings"
    print_endpoint "PUT $API_URL/settings/general"
    
    response=$(curl -s -w "%{http_code}" -o tmp_update_general.json \
      -X PUT "$API_URL/settings/general" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "full_name": "Updated Test User"
    }')
    
    check_response "$response" "200" "Update general settings"
    
    sleep 1
    
    # Step 3: Verify Update in /me
    print_step "Verify Name Update in /me"
    print_endpoint "GET $API_URL/me"
    
    response=$(curl -s -w "%{http_code}" -o tmp_me_after_update.json \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      "$API_URL/me")
    
    check_response "$response" "200" "Fetch user after update"
    validate_json_field "tmp_me_after_update.json" ".name" "Updated Test User" "Updated name"
    
    sleep 1
    
    # Step 4: Update Notification Settings
    print_step "Update Notification Settings"
    print_endpoint "PUT $API_URL/settings/notifications"
    
    response=$(curl -s -w "%{http_code}" -o tmp_update_notifications.json \
      -X PUT "$API_URL/settings/notifications" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "review_queue_reminder": "DAILY",
        "rejected_content_summary": true,
        "team_activity_digest": true,
        "delivery_channels": "in-app"
    }')
    
    check_response "$response" "200" "Update notification settings"
    
    sleep 1
    
    # Step 5: Verify Notification Settings
    print_step "Verify Notification Settings"
    print_endpoint "GET $API_URL/settings"
    
    response=$(curl -s -w "%{http_code}" -o tmp_settings_after_notif.json \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      "$API_URL/settings")
    
    check_response "$response" "200" "Fetch settings after notification update"
    validate_json_field "tmp_settings_after_notif.json" ".notification_settings.review_queue_reminder" "DAILY" "Queue reminder frequency"
}

# ============================================================================
# Test Flow: Team Management
# ============================================================================

test_team_flow() {
    print_header "TEAM MANAGEMENT FLOW"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "ACCESS_TOKEN not set. Run auth flow first."
        exit 1
    fi
    
    print_step "Team Flow - Placeholder"
    echo "⚠️  Team flow tests not yet implemented"
    # Add your team-related tests here
}

# ============================================================================
# Parse Arguments
# ============================================================================

parse_arguments() {
    for arg in "$@"; do
        case $arg in
            --clean-db)
                CLEAN_DB=true
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --flow=*)
                FLOW="${arg#*=}"
                shift
                ;;
            --help)
                head -n 18 "$0" | tail -n 16
                exit 0
                ;;
            *)
                echo "Unknown option: $arg"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    parse_arguments "$@"
    
    print_header "E2E TESTING SCRIPT"
    echo "Base URL: $BASE_URL"
    echo "API URL: $API_URL"
    echo "Email: $EMAIL"
    echo "Flow: $FLOW"
    echo "Clean DB: $CLEAN_DB"
    echo "Debug: $DEBUG"
    
    cleanup_temp_files
    clean_database
    
    # Always check server health first
    test_server_health
    
    # Run requested flows
    case $FLOW in
        auth)
            test_auth_flow
            ;;
        settings)
            test_auth_flow
            test_settings_flow
            ;;
        team)
            test_auth_flow
            test_team_flow
            ;;
        all)
            test_auth_flow
            test_settings_flow
            test_team_flow
            ;;
        *)
            print_error "Unknown flow: $FLOW"
            echo "Valid flows: auth, settings, team, all"
            exit 1
            ;;
    esac
    
    # Print Summary
    print_header "TEST SUMMARY"
    echo "Total Test Cases: $CURRENT_TEST"
    echo "Total Endpoints Called: $TOTAL_ENDPOINTS"
    echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo ""
        echo "================================================================"
        echo -e "${GREEN}  ✅ ALL TESTS PASSED SUCCESSFULLY! 🎉${NC}"
        echo "================================================================"
    else
        echo ""
        echo "================================================================"
        echo -e "${RED}  ❌ SOME TESTS FAILED${NC}"
        echo "================================================================"
        exit 1
    fi
    
    cleanup_temp_files
}

# Run main function
main "$@"