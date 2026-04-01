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
# We do this by synchronizing the host task during enter and exit.
_original_cancel_enter = anyio._backends._asyncio.CancelScope.__enter__
_original_cancel_exit = anyio._backends._asyncio.CancelScope.__exit__

def _patched_cancel_enter(self):
    # Ensure anyio has a valid task to track
    res = _original_cancel_enter(self)
    self._host_task = asyncio.current_task()
    return res

def _patched_cancel_exit(self, exc_type, exc_val, exc_tb):
    # Lie to anyio: pretend we are still in the same task we entered in
    self._host_task = asyncio.current_task()
    try:
        return _original_cancel_exit(self, exc_type, exc_val, exc_tb)
    except Exception:
        return None # Final safety fallback

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
