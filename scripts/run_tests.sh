#!/bin/bash
#
# Run project tests
#
# NOTE: This script expects to be run from the project root with
# ./scripts/run_tests.sh

# Use default environment vars for localhost if not already set
export DM_API_URL=${DM_API_URL:=http://localhost:5000}
export DM_BUYER_FRONTEND_API_AUTH_TOKEN=${DM_BUYER_FRONTEND_API_AUTH_TOKEN:=myToken}
export DM_SEARCH_API_URL=${DM_SEARCH_API_URL:=http://localhost:5001}
export DM_BUYER_FRONTEND_SEARCH_API_AUTH_TOKEN=${DM_BUYER_FRONTEND_SEARCH_API_AUTH_TOKEN:=myToken}

echo "Environment variables in use:"
env | grep DM_

set -o pipefail

function display_result {
  RESULT=$1
  EXIT_STATUS=$2
  TEST=$3

  if [ $RESULT -ne 0 ]; then
    echo -e "\033[31m$TEST failed\033[0m"
    exit $EXIT_STATUS
  else
    echo -e "\033[32m$TEST passed\033[0m"
  fi
}

pep8 .
display_result $? 2 "Code style check"

npm run --silent frontend-build:production
display_result $? 1 "Build of front end static assets"

py.test $@
display_result $? 3 "Python unit tests"

npm test
display_result $? 4 "JavaScript unit tests"
