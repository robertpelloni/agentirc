import sys
import asyncio
import typing
import unittest.mock
from dotenv import load_dotenv

# Load environment variables first (with override to ensure local .env wins)
load_dotenv(override=True)

# --- ULTIMATE PYTHON 3.14 COMPATIBILITY PATCH ---

# 1. Patch anyio to use native asyncio threads
import anyio.to_thread
async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)
anyio.to_thread.run_sync = patched_run_sync

# 2. Patch asyncio.current_task to return unique dummy tasks if None
# This prevents weakref errors and ensures each call has its own identity key for anyio.
_original_current_task = asyncio.current_task

class DummyTask:
    def __init__(self):
        self._must_cancel = False
        self._cancelling = 0
    def cancelling(self): return self._cancelling
    def uncancel(self): return 0
    def __bool__(self): return True
    def __getattr__(self, name): return None

def _patched_current_task(loop=None):
    task = _original_current_task(loop)
    if task is None:
        # Return a fresh dummy task for unique identity
        return DummyTask()
    return task
asyncio.current_task = _patched_current_task

# 3. Patch asyncio.timeouts.Timeout to handle missing tasks gracefully
import asyncio.timeouts
_original_timeout_enter = asyncio.timeouts.Timeout.__aenter__
_original_timeout_exit = asyncio.timeouts.Timeout.__aexit__

async def _patched_timeout_enter(self):
    try:
        return await _original_timeout_enter(self)
    except RuntimeError as e:
        if "Timeout should be used inside a task" in str(e):
            self._state = asyncio.timeouts._State.ENTERED
            self._task = asyncio.current_task()
            self._cancelling = 0
            return self
        raise e

async def _patched_timeout_exit(self, exc_type, exc_val, exc_tb):
    if self._state == asyncio.timeouts._State.CREATED:
        return None
    try:
        return await _original_timeout_exit(self, exc_type, exc_val, exc_tb)
    except (AssertionError, RuntimeError):
        # Python 3.14 state machine might be in a weird state
        return None

asyncio.timeouts.Timeout.__aenter__ = _patched_timeout_enter
asyncio.timeouts.Timeout.__aexit__ = _patched_timeout_exit

# -------------------------------------------------

# Now start Chainlit
from chainlit.cli import cli

if __name__ == "__main__":
    # Force the arguments for chainlit run app.py (Removed -w for stability)
    sys.argv = ["chainlit", "run", "app.py"]
    sys.exit(cli())
