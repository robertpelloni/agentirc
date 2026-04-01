import sys
import asyncio
import typing
from dotenv import load_dotenv

# Load environment variables first
load_dotenv(override=True)

# --- ULTIMATE PYTHON 3.14 COMPATIBILITY NUKE (V4) ---

class DummyTask:
    def __init__(self):
        self._must_cancel = False
        self._cancelling = 0
    def cancelling(self): return self._cancelling
    def uncancel(self): return 0
    def __bool__(self): return True
    def __hash__(self): return hash("dummy")
    def __eq__(self, other): return isinstance(other, DummyTask)
    def __getattr__(self, name): return None

GLOBAL_DUMMY_TASK = DummyTask()

# 1. Patch anyio to use native asyncio threads
import anyio.to_thread
async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)
anyio.to_thread.run_sync = patched_run_sync

# 2. Force AnyIO CancelScope to always pass identity checks
import anyio._backends._asyncio
_original_cancel_enter = anyio._backends._asyncio.CancelScope.__enter__
_original_cancel_exit = anyio._backends._asyncio.CancelScope.__exit__

def _patched_cancel_enter(self):
    task = asyncio.current_task() or GLOBAL_DUMMY_TASK
    self._host_task = task
    try:
        return _original_cancel_enter(self)
    except (TypeError, KeyError):
        self._active = True
        self._tasks.add(task)
        return self

def _patched_cancel_exit(self, exc_type, exc_val, exc_tb):
    if self._host_task is GLOBAL_DUMMY_TASK:
        pass 
    else:
        if asyncio.current_task() is None:
            self._host_task = None 
            
    try:
        return _original_cancel_exit(self, exc_type, exc_val, exc_tb)
    except Exception:
        return None

anyio._backends._asyncio.CancelScope.__enter__ = _patched_cancel_enter
anyio._backends._asyncio.CancelScope.__exit__ = _patched_cancel_exit

# 3. Force asyncio.timeouts to always pass state checks
import asyncio.timeouts
_original_timeout_enter = asyncio.timeouts.Timeout.__aenter__
_original_timeout_exit = asyncio.timeouts.Timeout.__aexit__

async def _patched_timeout_enter(self):
    try:
        return await _original_timeout_enter(self)
    except RuntimeError:
        self._state = asyncio.timeouts._State.ENTERED
        self._task = asyncio.current_task() or GLOBAL_DUMMY_TASK
        self._cancelling = 0
        return self

async def _patched_timeout_exit(self, exc_type, exc_val, exc_tb):
    if self._state == asyncio.timeouts._State.CREATED:
        return None
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
