#!/bin/bash
if [ -n "$VIRTUAL_ENV" ]; then
  echo "Already in virtual environment $VIRTUAL_ENV"
else
  source ./venv/bin/activate 2>/dev/null && echo "Virtual environment activated."
fi

# Use default environment vars for localhost if not already set
export DM_DATA_API_URL=${DM_API_URL:=http://localhost:5000}
export DM_DATA_API_AUTH_TOKEN=${DM_BUYER_FRONTEND_API_AUTH_TOKEN:=myToken}
export DM_SEARCH_API_URL=${DM_SEARCH_API_URL:=http://localhost:5001}
export DM_SEARCH_API_AUTH_TOKEN=${DM_SEARCH_API_AUTH_TOKEN:=myToken}
export ES_ENABLED=${ES_ENABLED:=True}

echo "Environment variables in use:" 
env | grep DM_

python application.py runserver
