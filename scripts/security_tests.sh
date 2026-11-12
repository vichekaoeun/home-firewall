#!/usr/bin/env bash

# Network Security Gateway - Automated Security Tests

passed=0
failed=0

run_allowed() {
    local name="$1"
    shift

    printf "Testing %-45s" "$name"

    if "$@" >/dev/null 2>&1; then
        echo " PASS"
        ((passed++))
    else
        echo " FAIL (expected connection to succeed)"
        ((failed++))
    fi
}

run_blocked() {
    local name="$1"
    shift

    printf "Testing %-45s" "$name"

    if "$@" >/dev/null 2>&1; then
        echo " FAIL (connection unexpectedly succeeded)"
        ((failed++))
    else
        echo " PASS (connection blocked)"
        ((passed++))
    fi
}

http_test() {
    local service="$1"
    local address="$2"

    docker compose exec -T "$service" \
        curl -fsS -I --connect-timeout 3 --max-time 4 \
        "http://${address}"
}

tcp_test() {
    local service="$1"
    local address="$2"
    local port="$3"

    docker compose exec -T "$service" python3 -c '
import socket
import sys

sock = socket.create_connection(
    (sys.argv[1], int(sys.argv[2])),
    timeout=2
)
sock.close()
' "$address" "$port"
}

echo "========================================"
echo " Network Security Gateway - Test Suite"
echo "========================================"
echo

echo "[ AUTHORIZED CONNECTIONS ]"

run_allowed "A1 External -> Web (DNAT)" \
    http_test external-client 10.10.10.2:8080

run_allowed "A2 Web -> Internal API" \
    http_test web-server 10.10.30.10:8080

run_allowed "A3 Internal API -> Database" \
    tcp_test internal-api 10.10.40.20 5432

echo
echo "[ UNAUTHORIZED CONNECTIONS ]"

run_blocked "B1 External -> Internal API" \
    http_test external-client 10.10.30.10:8080

run_blocked "B2 External -> Database" \
    tcp_test external-client 10.10.40.20 5432

run_blocked "B3 Web -> Database" \
    tcp_test web-server 10.10.40.20 5432

echo
echo "========================================"
echo " Results: $passed passed, $failed failed"
echo "========================================"

if [ "$failed" -gt 0 ]; then
    exit 1
fi
