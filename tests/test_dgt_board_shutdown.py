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

    async def test_stop_tolerates_serial_connection_already_being_closed(self):
        loop = asyncio.get_running_loop()
        board = DgtBoard("/dev/test", False, False, False, loop)
        serial = Mock()
        serial.close.side_effect = TypeError("descriptor already closed")
        board.serial = serial

        await board.stop()

        self.assertIsNone(board.serial)
        serial.close.assert_called_once_with()

    async def test_read_tolerates_descriptor_closed_by_shutdown(self):
        loop = asyncio.get_running_loop()
        board = DgtBoard("/dev/test", False, False, False, loop)
        board.serial = Mock()
        board.serial.read.side_effect = TypeError("descriptor already closed")

        self.assertEqual(board._read_serial(), b"")

    async def test_stop_tolerates_reader_failing_during_serial_close(self):
        loop = asyncio.get_running_loop()
        board = DgtBoard("/dev/test", False, False, False, loop)

        async def reader_failed():
            raise TypeError("descriptor already closed")

        board.incoming_board_task = asyncio.create_task(reader_failed())

        await board.stop()

        self.assertTrue(board.incoming_board_task.done())
