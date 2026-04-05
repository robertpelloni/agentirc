@echo off
echo Building AgentIRC...
pip install -r requirements.txt
python -m py_compile app.py run.py simulator_core.py tests\test_simulator_core.py
python -m unittest discover -s tests -v
echo Build and test pass complete.
pause
