#!/bin/sh
# load_testing.sh is under development, this version might not work 

if command -v ab &>/dev/null; then
  echo "ab is installed at: $(command -v ab)"
else
  echo "Error: ab is not installed." >&2  # Redirect to stderr
  exit 1
fi

read -p "Enter user UUID for GET queries" user_id 

echo "Starting awesome-notes load testing"

echo "Testing user_service"
ab -k -c 5 -n 15000 -C "access_token=$access_token" "http://127.0.0.1:8001/user/"
ab -k -c 5 -n 20000 -C "access_token=$access_token" "http://127.0.0.1:8001/user/by-id/5ae8f6f2-790b-4c91-a4ae-ccf7c2874919"
