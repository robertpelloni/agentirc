@echo off
echo Building AgentIRC...
pip install -r requirements.txt
python -m py_compile app.py run.py bridge_connectors.py bridge_runtime.py simulator_core.py tests\test_simulator_core.py tests\test_bridge_connectors.py
python -m unittest discover -s tests -v
echo Build and test pass complete.
pause
