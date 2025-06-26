#!/bin/bash

# Data Governance API - Comprehensive Test Script
# Tests the entire environment including Docker, database, API, and data integrity

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="http://localhost:8000"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="data_governance"
DB_USER="postgres"
DB_PASSWORD="postgres123"
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD="redis123"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TEST_RESULTS=()

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    TEST_RESULTS+=("PASS: $1")
}

error() {
    echo -e "${RED}✗${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    TEST_RESULTS+=("FAIL: $1")
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    log "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            success "$service_name is ready"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to test HTTP endpoint
test_http_endpoint() {
    local url=$1
    local expected_status=$2
    local description=$3
    
    log "Testing: $description"
    
    local response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        success "$description (HTTP $response)"
        return 0
    else
        error "$description (Expected HTTP $expected_status, got $response)"
        return 1
    fi
}

# Function to test database connection
test_database_connection() {
    log "Testing database connection..."
    
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
        success "Database connection successful"
        return 0
    else
        error "Database connection failed"
        return 1
    fi
}

# Function to test Redis connection
test_redis_connection() {
    log "Testing Redis connection..."
    
    if redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping >/dev/null 2>&1; then
        success "Redis connection successful"
        return 0
    else
        error "Redis connection failed"
        return 1
    fi
}

# Function to validate mock data
validate_mock_data() {
    log "Validating mock data integrity..."
    
    # Test data objects count
    local data_objects_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM governance.data_objects;" 2>/dev/null | xargs)
    
    if [ "$data_objects_count" -ge "5" ]; then
        success "Data objects count: $data_objects_count"
    else
        error "Insufficient data objects: $data_objects_count (expected >= 5)"
    fi
    
    # Test data contracts count
    local contracts_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM governance.data_contracts;" 2>/dev/null | xargs)
    
    if [ "$contracts_count" -ge "2" ]; then
        success "Data contracts count: $contracts_count"
    else
        error "Insufficient data contracts: $contracts_count (expected >= 2)"
    fi
    
    # Test quality metrics count
    local metrics_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM quality.quality_metrics;" 2>/dev/null | xargs)
    
    if [ "$metrics_count" -ge "5" ]; then
        success "Quality metrics count: $metrics_count"
    else
        error "Insufficient quality metrics: $metrics_count (expected >= 5)"
    fi
    
    # Test lineage relationships
    local lineage_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM lineage.data_lineage;" 2>/dev/null | xargs)
    
    if [ "$lineage_count" -ge "4" ]; then
        success "Data lineage count: $lineage_count"
    else
        error "Insufficient lineage relationships: $lineage_count (expected >= 4)"
    fi
    
    # Test access policies
    local policies_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM security.access_policies;" 2>/dev/null | xargs)
    
    if [ "$policies_count" -ge "6" ]; then
        success "Access policies count: $policies_count"
    else
        error "Insufficient access policies: $policies_count (expected >= 6)"
    fi
}

# Function to test API endpoints
test_api_endpoints() {
    log "Testing API endpoints..."
    
    # Health check
    test_http_endpoint "$API_BASE_URL/health" "200" "Health check endpoint"
    
    # Metrics endpoint
    test_http_endpoint "$API_BASE_URL/metrics" "200" "Metrics endpoint"
    
    # OpenAPI documentation
    test_http_endpoint "$API_BASE_URL/docs" "200" "Swagger UI documentation"
    test_http_endpoint "$API_BASE_URL/redoc" "200" "ReDoc documentation"
    test_http_endpoint "$API_BASE_URL/openapi.json" "200" "OpenAPI specification"
    
    # Data objects endpoints
    test_http_endpoint "$API_BASE_URL/api/v1/data-objects/" "200" "Data objects list endpoint"
    test_http_endpoint "$API_BASE_URL/api/v1/data-objects/search?q=customer" "200" "Data objects search endpoint"
    
    # Data contracts endpoints
    test_http_endpoint "$API_BASE_URL/api/v1/data-contracts/" "200" "Data contracts list endpoint"
    
    # Quality metrics endpoints
    test_http_endpoint "$API_BASE_URL/api/v1/quality/metrics/" "200" "Quality metrics list endpoint"
    
    # Lineage endpoints
    test_http_endpoint "$API_BASE_URL/api/v1/lineage/" "200" "Data lineage list endpoint"
    
    # Access policies endpoints
    test_http_endpoint "$API_BASE_URL/api/v1/access-policies/" "200" "Access policies list endpoint"
}

# Function to test API functionality with data
test_api_functionality() {
    log "Testing API functionality with mock data..."
    
    # Test getting specific data object
    local first_object_id=$(curl -s "$API_BASE_URL/api/v1/data-objects/" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') else '')" 2>/dev/null)
    
    if [ -n "$first_object_id" ]; then
        test_http_endpoint "$API_BASE_URL/api/v1/data-objects/$first_object_id" "200" "Get specific data object"
    else
        error "Could not retrieve data object ID for detailed testing"
    fi
    
    # Test pagination
    test_http_endpoint "$API_BASE_URL/api/v1/data-objects/?page=1&size=2" "200" "Data objects pagination"
    
    # Test filtering
    test_http_endpoint "$API_BASE_URL/api/v1/data-objects/?object_type=table" "200" "Data objects filtering by type"
    test_http_endpoint "$API_BASE_URL/api/v1/data-objects/?classification=confidential" "200" "Data objects filtering by classification"
    
    # Test quality metrics filtering
    test_http_endpoint "$API_BASE_URL/api/v1/quality/metrics/?metric_type=completeness" "200" "Quality metrics filtering by type"
    test_http_endpoint "$API_BASE_URL/api/v1/quality/metrics/?status=passed" "200" "Quality metrics filtering by status"
}

# Function to test Docker services
test_docker_services() {
    log "Testing Docker services..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running"
        return 1
    fi
    success "Docker is running"
    
    # Check if docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        error "docker-compose is not available"
        return 1
    fi
    success "docker-compose is available"
    
    # Check running containers
    local running_containers=$(docker-compose ps --services --filter "status=running" 2>/dev/null | wc -l)
    
    if [ "$running_containers" -ge "3" ]; then
        success "Docker services running: $running_containers"
    else
        warning "Limited Docker services running: $running_containers"
    fi
}

# Function to run performance tests
test_performance() {
    log "Running basic performance tests..."
    
    # Test API response time
    local start_time=$(date +%s%N)
    curl -s "$API_BASE_URL/health" >/dev/null
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    if [ "$response_time" -lt "1000" ]; then
        success "API response time: ${response_time}ms (good)"
    elif [ "$response_time" -lt "3000" ]; then
        warning "API response time: ${response_time}ms (acceptable)"
    else
        error "API response time: ${response_time}ms (slow)"
    fi
    
    # Test database query performance
    local db_start_time=$(date +%s%N)
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM governance.data_objects;" >/dev/null 2>&1
    local db_end_time=$(date +%s%N)
    local db_response_time=$(( (db_end_time - db_start_time) / 1000000 ))
    
    if [ "$db_response_time" -lt "500" ]; then
        success "Database query time: ${db_response_time}ms (good)"
    elif [ "$db_response_time" -lt "2000" ]; then
        warning "Database query time: ${db_response_time}ms (acceptable)"
    else
        error "Database query time: ${db_response_time}ms (slow)"
    fi
}

# Function to test data integrity
test_data_integrity() {
    log "Testing data integrity and relationships..."
    
    # Test foreign key relationships
    local orphaned_contracts=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM governance.data_contracts dc LEFT JOIN governance.data_objects do ON dc.data_object_id = do.id WHERE do.id IS NULL;" 2>/dev/null | xargs)
    
    if [ "$orphaned_contracts" = "0" ]; then
        success "No orphaned data contracts"
    else
        error "Found $orphaned_contracts orphaned data contracts"
    fi
    
    # Test lineage integrity
    local invalid_lineage=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM lineage.data_lineage dl WHERE dl.source_object_id = dl.target_object_id;" 2>/dev/null | xargs)
    
    if [ "$invalid_lineage" = "0" ]; then
        success "No self-referencing lineage relationships"
    else
        error "Found $invalid_lineage self-referencing lineage relationships"
    fi
    
    # Test quality metrics data consistency
    local invalid_metrics=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM quality.quality_metrics WHERE metric_value < 0 OR metric_value > 100;" 2>/dev/null | xargs)
    
    if [ "$invalid_metrics" = "0" ]; then
        success "All quality metrics have valid values"
    else
        error "Found $invalid_metrics quality metrics with invalid values"
    fi
}

# Function to generate test report
generate_test_report() {
    log "Generating test report..."
    
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local success_rate=0
    
    if [ "$total_tests" -gt "0" ]; then
        success_rate=$(( (TESTS_PASSED * 100) / total_tests ))
    fi
    
    echo ""
    echo "=========================================="
    echo "           TEST REPORT SUMMARY"
    echo "=========================================="
    echo "Total Tests: $total_tests"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Success Rate: $success_rate%"
    echo ""
    
    if [ "$TESTS_FAILED" -eq "0" ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED! Environment is ready for use.${NC}"
    else
        echo -e "${RED}❌ Some tests failed. Please review the issues above.${NC}"
    fi
    
    echo ""
    echo "Detailed Results:"
    echo "==================="
    for result in "${TEST_RESULTS[@]}"; do
        if [[ $result == PASS:* ]]; then
            echo -e "${GREEN}$result${NC}"
        else
            echo -e "${RED}$result${NC}"
        fi
    done
    
    # Save report to file
    {
        echo "Data Governance API Test Report"
        echo "Generated: $(date)"
        echo "Total Tests: $total_tests"
        echo "Passed: $TESTS_PASSED"
        echo "Failed: $TESTS_FAILED"
        echo "Success Rate: $success_rate%"
        echo ""
        echo "Detailed Results:"
        for result in "${TEST_RESULTS[@]}"; do
            echo "$result"
        done
    } > test_report.txt
    
    success "Test report saved to test_report.txt"
}

# Main test execution
main() {
    echo "=========================================="
    echo "    Data Governance API Test Suite"
    echo "=========================================="
    echo ""
    
    log "Starting comprehensive environment tests..."
    
    # Check prerequisites
    log "Checking prerequisites..."
    
    if ! command -v curl >/dev/null 2>&1; then
        error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v nc >/dev/null 2>&1; then
        error "netcat (nc) is required but not installed"
        exit 1
    fi
    
    if ! command -v psql >/dev/null 2>&1; then
        error "PostgreSQL client (psql) is required but not installed"
        exit 1
    fi
    
    if ! command -v redis-cli >/dev/null 2>&1; then
        warning "Redis client (redis-cli) not found, skipping Redis tests"
    fi
    
    success "Prerequisites check completed"
    
    # Test Docker services
    test_docker_services
    
    # Wait for services to be ready
    wait_for_service $DB_HOST $DB_PORT "PostgreSQL"
    wait_for_service $REDIS_HOST $REDIS_PORT "Redis"
    wait_for_service "localhost" "8000" "Data Governance API"
    
    # Test database connection
    test_database_connection
    
    # Test Redis connection (if available)
    if command -v redis-cli >/dev/null 2>&1; then
        test_redis_connection
    fi
    
    # Validate mock data
    validate_mock_data
    
    # Test data integrity
    test_data_integrity
    
    # Test API endpoints
    test_api_endpoints
    
    # Test API functionality
    test_api_functionality
    
    # Run performance tests
    test_performance
    
    # Generate final report
    generate_test_report
    
    # Exit with appropriate code
    if [ "$TESTS_FAILED" -eq "0" ]; then
        exit 0
    else
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Data Governance API Test Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  help     Show this help message"
        echo "  quick    Run quick tests only"
        echo "  full     Run full test suite (default)"
        echo ""
        exit 0
        ;;
    "quick")
        log "Running quick tests only..."
        test_database_connection
        test_http_endpoint "$API_BASE_URL/health" "200" "Health check endpoint"
        generate_test_report
        ;;
    "full"|"")
        main
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

