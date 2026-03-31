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

# 2. Patch asyncio.current_task to return a robust dummy task if None
# This prevents weakref errors and strict task checks.
_original_current_task = asyncio.current_task
def _patched_current_task(loop=None):
    task = _original_current_task(loop)
    if task is None:
        if not hasattr(_patched_current_task, "_dummy"):
            mock_task = unittest.mock.MagicMock(spec=asyncio.Task)
            mock_task.cancelling.return_value = 0
            mock_task.uncancel.return_value = 0
            # Ensure it can be used in weakrefs if needed
            mock_task.__weakref__ = None 
            _patched_current_task._dummy = mock_task
        return _patched_current_task._dummy
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
            # Manually set state to ENTERED to satisfy __aexit__ assertion
            self._state = asyncio.timeouts._State.ENTERED
            self._task = asyncio.current_task()
            self._cancelling = 0
            return self
        raise e

async def _patched_timeout_exit(self, exc_type, exc_val, exc_tb):
    # If state is still CREATED, it means __aenter__ failed or was bypassed
    if self._state == asyncio.timeouts._State.CREATED:
        return None
    return await _original_timeout_exit(self, exc_type, exc_val, exc_tb)

asyncio.timeouts.Timeout.__aenter__ = _patched_timeout_enter
asyncio.timeouts.Timeout.__aexit__ = _patched_timeout_exit

# -------------------------------------------------

# Now start Chainlit
from chainlit.cli import cli

if __name__ == "__main__":
    # Force the arguments for chainlit run app.py -w
    sys.argv = ["chainlit", "run", "app.py", "-w"]
    sys.exit(cli())
