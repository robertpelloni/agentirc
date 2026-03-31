import sys
import asyncio
import typing
import unittest.mock

# --- ULTIMATE PYTHON 3.14 COMPATIBILITY PATCH ---

# 1. Patch anyio to use native asyncio threads
import anyio.to_thread
async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)
anyio.to_thread.run_sync = patched_run_sync

# 2. Patch asyncio.current_task to return a dummy task if None
# This solves the "Timeout should be used inside a task" error in asyncio.timeouts
# and weakref errors in anyio by ensuring a task-like object always exists.
_original_current_task = asyncio.current_task
def _patched_current_task(loop=None):
    task = _original_current_task(loop)
    if task is None:
        # Create a persistent dummy task object
        if not hasattr(_patched_current_task, "_dummy"):
            mock_task = unittest.mock.MagicMock(spec=asyncio.Task)
            mock_task.__bool__.return_value = True
            _patched_current_task._dummy = mock_task
        return _patched_current_task._dummy
    return task
asyncio.current_task = _patched_current_task

# 3. Patch asyncio.timeouts to be lenient
import asyncio.timeouts
_original_timeout_enter = asyncio.timeouts.Timeout.__aenter__
async def _patched_timeout_enter(self):
    try:
        return await _original_timeout_enter(self)
    except RuntimeError:
        return self
asyncio.timeouts.Timeout.__aenter__ = _patched_timeout_enter

# -------------------------------------------------

# Now start Chainlit
from chainlit.cli import cli

if __name__ == "__main__":
    # Force the arguments for chainlit run app.py -w
    sys.argv = ["chainlit", "run", "app.py", "-w"]
    sys.exit(cli())
