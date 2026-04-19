#!/bin/bash
export CHAINLIT_AUTH_SECRET="SUPER_SECRET_DUMMY_KEY_FOR_TESTS"
export AGENTIRC_USER_ADMIN="supersecret"
# Chainlit might run in foreground, so run it in background
chainlit run app.py -h --port 8000 > chainlit.log 2>&1 &
