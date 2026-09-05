import asyncio
import unittest

from picochess import gather_main_tasks, track_event_task, wait_for_shutdown_cleanup


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

    async def test_intentional_shutdown_waits_for_cleanup_completion(self):
        shutdown_requested = asyncio.Event()
        shutdown_complete = asyncio.Event()
        shutdown_requested.set()

        wait_task = asyncio.create_task(wait_for_shutdown_cleanup(shutdown_requested, shutdown_complete))
        await asyncio.sleep(0)
        self.assertFalse(wait_task.done())

        shutdown_complete.set()
        await wait_task

    async def test_normal_task_completion_does_not_wait_for_shutdown_cleanup(self):
        shutdown_requested = asyncio.Event()
        shutdown_complete = asyncio.Event()

        await wait_for_shutdown_cleanup(shutdown_requested, shutdown_complete)

    async def test_tracked_event_task_is_retained_until_completion(self):
        event_tasks = set()
        release_task = asyncio.Event()
        task = asyncio.create_task(release_task.wait())

        track_event_task(task, event_tasks)
        self.assertIn(task, event_tasks)

        release_task.set()
        await task
        await asyncio.sleep(0)
        self.assertNotIn(task, event_tasks)

    async def test_tracked_event_task_exception_is_retrieved_and_logged(self):
        event_tasks = set()

        async def fail():
            raise RuntimeError("event failed")

        with self.assertLogs("picochess", level="ERROR") as captured:
            task = asyncio.create_task(fail())
            track_event_task(task, event_tasks)
            await asyncio.sleep(0)
            await asyncio.sleep(0)

        self.assertNotIn(task, event_tasks)
        self.assertIn("Unhandled exception while processing main event", captured.output[0])
