@echo off
echo Building AgentIRC...
pip install -r requirements.txt
python -m py_compile app.py run.py bridge_connectors.py bridge_runtime.py irc_bridge_runtime.py simulator_core.py simulator_tools.py tests\test_simulator_core.py tests\test_bridge_connectors.py tests\test_irc_bridge_runtime.py tests\test_live_integration.py
python -m unittest discover -s tests -v
echo Build and test pass complete.
pause
