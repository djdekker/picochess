import asyncio
import unittest

from picochess import gather_main_tasks


class TestMainTaskShutdown(unittest.IsolatedAsyncioTestCase):
    async def test_expected_task_cancellation_is_clean_during_shutdown(self):
        shutdown_requested = asyncio.Event()
        shutdown_requested.set()
        task = asyncio.create_task(asyncio.sleep(60))
        task.cancel()

        await gather_main_tasks({task}, shutdown_requested)

    async def test_unexpected_task_cancellation_still_propagates(self):
        shutdown_requested = asyncio.Event()
        task = asyncio.create_task(asyncio.sleep(60))
        task.cancel()

        with self.assertRaises(asyncio.CancelledError):
            await gather_main_tasks({task}, shutdown_requested)

    async def test_application_exception_still_propagates_during_shutdown(self):
        shutdown_requested = asyncio.Event()
        shutdown_requested.set()

        async def fail():
            raise RuntimeError("task failed")

        with self.assertRaisesRegex(RuntimeError, "task failed"):
            await gather_main_tasks({asyncio.create_task(fail())}, shutdown_requested)
