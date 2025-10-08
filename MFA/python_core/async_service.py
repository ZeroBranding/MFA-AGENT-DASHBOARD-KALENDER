import asyncio, signal
from contextlib import asynccontextmanager

class Service:
    def __init__(self) -> None:
        self._shutdown = asyncio.Event()
        self._cleanup = []

    def on_shutdown(self, fn):
        self._cleanup.append(fn)

    async def _graceful(self):
        for fn in reversed(self._cleanup):
            try:
                await fn()
            except Exception as e:
                print(f"[graceful] cleanup error: {e}")

    async def run(self, main):
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._shutdown.set)

        main_task = asyncio.create_task(main())
        stop_task = asyncio.create_task(self._shutdown.wait())

        done, _ = await asyncio.wait(
            {main_task, stop_task}, return_when=asyncio.FIRST_COMPLETED
        )
        if stop_task in done:
            main_task.cancel()
        await self._graceful()
