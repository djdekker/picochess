import asyncio
import unittest
from unittest.mock import Mock

from dgt.board import DgtBoard


class TestDgtBoardShutdown(unittest.IsolatedAsyncioTestCase):
    async def test_stop_ends_reader_and_closes_serial_connection(self):
        loop = asyncio.get_running_loop()
        board = DgtBoard("/dev/test", False, False, False, loop)
        serial = Mock()
        board.serial = serial
        board._read_serial = Mock(return_value=b"")

        board.run()
        await asyncio.sleep(0)
        await board.stop()

        self.assertTrue(board.stop_requested.is_set())
        self.assertTrue(board.incoming_board_task.done())
        self.assertIsNone(board.serial)
        serial.close.assert_called_once_with()

    async def test_run_clears_previous_stop_request(self):
        loop = asyncio.get_running_loop()
        board = DgtBoard("/dev/test", False, False, False, loop)
        board.stop_requested.set()
        board._process_incoming_board_forever = Mock()

        board.run()
        await board.incoming_board_task

        self.assertFalse(board.stop_requested.is_set())
        board._process_incoming_board_forever.assert_called_once_with()
