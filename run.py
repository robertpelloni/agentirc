import sys
import asyncio
import typing
import anyio._backends._asyncio
import asyncio.timeouts
from dotenv import load_dotenv

# Load environment variables first
load_dotenv(override=True)

# --- ULTIMATE PYTHON 3.14 COMPATIBILITY NUKE (V3) ---

# 1. Patch anyio to use native asyncio threads
import anyio.to_thread
async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)
anyio.to_thread.run_sync = patched_run_sync

# 2. Force AnyIO CancelScope to always pass identity checks
# We completely override the enter/exit logic to handle Python 3.14 context issues.
def _patched_cancel_enter(self):
    if self._host_task is not None:
        raise RuntimeError("Already entered")
    
    task = asyncio.current_task()
    self._host_task = task
    
    if task is not None:
        try:
            # Try to register with anyio's internal task states
            from anyio._backends._asyncio import _task_states
            if task not in _task_states:
                from anyio._backends._asyncio import TaskState
                _task_states[task] = TaskState(None)
        except Exception:
            pass
            
    self._timeout_handle = None
    if self._deadline != float('inf'):
        loop = asyncio.get_running_loop()
        self._timeout_handle = loop.call_at(self._deadline, self._cancel_by_timeout)
        
    return self

def _patched_cancel_exit(self, exc_type, exc_val, exc_tb):
    if self._timeout_handle:
        self._timeout_handle.cancel()
        self._timeout_handle = None
        
    self._host_task = None
    return None

anyio._backends._asyncio.CancelScope.__enter__ = _patched_cancel_enter
anyio._backends._asyncio.CancelScope.__exit__ = _patched_cancel_exit

# 3. Force asyncio.timeouts to always pass state checks
_original_timeout_enter = asyncio.timeouts.Timeout.__aenter__
_original_timeout_exit = asyncio.timeouts.Timeout.__aexit__

async def _patched_timeout_enter(self):
    try:
        return await _original_timeout_enter(self)
    except RuntimeError:
        # Manually initialize state if native enter fails due to task context
        self._state = asyncio.timeouts._State.ENTERED
        self._task = asyncio.current_task()
        self._cancelling = 0
        return self

async def _patched_timeout_exit(self, exc_type, exc_val, exc_tb):
    # Force state to valid before calling original exit
    if self._state == asyncio.timeouts._State.CREATED:
        return None
    self._state = asyncio.timeouts._State.ENTERED
    try:
        return await _original_timeout_exit(self, exc_type, exc_val, exc_tb)
    except Exception:
        return None

asyncio.timeouts.Timeout.__aenter__ = _patched_timeout_enter
asyncio.timeouts.Timeout.__aexit__ = _patched_timeout_exit

# 4. Global Sniffio Nuke
import sniffio
sniffio.current_async_library = lambda *args, **kwargs: "asyncio"

# -------------------------------------------------

# Now start Chainlit
from chainlit.cli import cli

if __name__ == "__main__":
    # Force the arguments for chainlit run app.py
    sys.argv = ["chainlit", "run", "app.py"]
    sys.exit(cli())
