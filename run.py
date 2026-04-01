import sys
import asyncio
import typing
import anyio._backends._asyncio
import sniffio
from dotenv import load_dotenv

# Load environment variables first (with override to ensure local .env wins)
load_dotenv(override=True)

# --- ULTIMATE PYTHON 3.14 COMPATIBILITY NUKE ---

# 1. Global Sniffio Nuke: Force it to ALWAYS return 'asyncio'
# This fixes the OpenAI SDK and other libraries that use sniffio for detection.
def _ultimate_sniffio_patch(*args, **kwargs):
    return "asyncio"
sniffio.current_async_library = _ultimate_sniffio_patch

# 2. Patch anyio to use native asyncio threads
import anyio.to_thread
async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)
anyio.to_thread.run_sync = patched_run_sync

# 3. Bypass strict CancelScope task identity checks in anyio
_original_cancel_enter = anyio._backends._asyncio.CancelScope.__enter__
_original_cancel_exit = anyio._backends._asyncio.CancelScope.__exit__

def _patched_cancel_enter(self):
    try:
        return _original_cancel_enter(self)
    except TypeError as e:
        if "cannot create weak reference to 'NoneType' object" in str(e):
            return self
        raise e

def _patched_cancel_exit(self, exc_type, exc_val, exc_tb):
    try:
        return _original_cancel_exit(self, exc_type, exc_val, exc_tb)
    except (RuntimeError, TypeError) as e:
        if "Attempted to exit cancel scope in a different task" in str(e) or \
           "cannot create weak reference to 'NoneType' object" in str(e):
            if hasattr(self, '_restart_cancellation_in_parent'):
                try: self._restart_cancellation_in_parent()
                except: pass
            return None
        raise e

anyio._backends._asyncio.CancelScope.__enter__ = _patched_cancel_enter
anyio._backends._asyncio.CancelScope.__exit__ = _patched_cancel_exit

# 4. Patch asyncio.timeouts.Timeout to handle missing tasks gracefully
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
        return None

asyncio.timeouts.Timeout.__aenter__ = _patched_timeout_enter
asyncio.timeouts.Timeout.__aexit__ = _patched_timeout_exit

# -------------------------------------------------

# Now start Chainlit
from chainlit.cli import cli

if __name__ == "__main__":
    # Force the arguments for chainlit run app.py
    sys.argv = ["chainlit", "run", "app.py"]
    sys.exit(cli())
