import sys
import asyncio

# Aggressively patch anyio before Chainlit or Starlette can load it
import anyio.to_thread
import typing

async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)

anyio.to_thread.run_sync = patched_run_sync

# Now start Chainlit
from chainlit.cli import cli

if __name__ == "__main__":
    # Force the arguments for chainlit run app.py -w
    sys.argv = ["chainlit", "run", "app.py", "-w"]
    sys.exit(cli())
