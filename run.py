import sys
import asyncio
import typing

# --- Python 3.14 Deep Compatibility Patches ---

# 1. Patch anyio to use native asyncio threads
import anyio.to_thread
async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)
anyio.to_thread.run_sync = patched_run_sync

# 2. Patch asyncio.timeouts to be lenient on Python 3.14
# This prevents the "Timeout should be used inside a task" crash in engineio
import asyncio.timeouts
original_timeout_enter = asyncio.timeouts.Timeout.__aenter__

async def patched_timeout_enter(self):
    try:
        return await original_timeout_enter(self)
    except RuntimeError as e:
        if "Timeout should be used inside a task" in str(e):
            # Fallback for code running outside a formal task (common in engineio/uvicorn startup)
            return self
        raise e

asyncio.timeouts.Timeout.__aenter__ = patched_timeout_enter

# ----------------------------------------------

# Now start Chainlit
from chainlit.cli import cli

if __name__ == "__main__":
    # Force the arguments for chainlit run app.py -w
    sys.argv = ["chainlit", "run", "app.py", "-w"]
    sys.exit(cli())
