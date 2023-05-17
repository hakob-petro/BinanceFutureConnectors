# -*- coding: utf-8 -*-

# Standard modules
import time
import threading
import asyncio
import queue
from typing import List, Tuple

# Project-modules
from network import ThreadedWS, AsyncWSv1, AsyncWSv2
from constants import ProjectConstants

__all__ = [
    "run_MWMT",
    "run_MWST",
    "run_SWST"
]


def run_MWMT(ticker: str, timeout: int, num_thread: int) -> Tuple[List[List[int]], ...]:
    """
    Run multiple websockets via multiple threads. For each connection will be opened a new websocket,
    which will be managed by his own thread.

    :param ticker: future's ticker
    :type ticker: str
    :param timeout: lifetime in seconds of each connection
    :type timeout: int
    :param num_thread: number of connections
    :type num_thread: int
    :return Tuple[List[List[int]], ...]: list of update ids, client timestamps and delays for each connection
    """
    threads_l = list()
    client_timestamps_l = [queue.Queue() for _ in range(num_thread)]
    delays_l = [queue.Queue() for _ in range(num_thread)]
    update_ids_l = [queue.Queue() for _ in range(num_thread)]

    for client_timestamps, delays, update_ids in zip(client_timestamps_l, delays_l, update_ids_l):
        thr = threading.Thread(target=ThreadedWS, args=(
            ProjectConstants.BINANCE_FUTURES_WS, ticker,
            client_timestamps, delays, update_ids))
        threads_l.append(thr)
        thr.start()

    time.sleep(timeout)
    for thr in threads_l:
        thr.join(0)

    client_timestamps_l = [list(time_q.queue) for time_q in client_timestamps_l]
    delays_l = [list(delays_q.queue) for delays_q in delays_l]
    update_ids_l = [list(updates_q.queue) for updates_q in update_ids_l]
    return update_ids_l, client_timestamps_l, delays_l


def run_MWST(ticker: str, timeout: int, num_coro: int) -> Tuple[List[List[int]], ...]:
    """
    Run multiple websockets via single threads. For each connection will be opened a new websocket,
    and each socket will recive data asyncronously .

    :param ticker: future's ticker
    :type ticker: str
    :param timeout: lifetime in seconds of each connection
    :type timeout: int
    :param num_coro: number of coroutines
    :type num_coro: int
    :return Tuple[List[List[int]], ...]: list of update ids, client timestamps and delays for each connection
    """

    async def runner():
        async_sockets = []
        tasks = []

        for _ in range(num_coro):
            async_sockets.append(AsyncWSv1(ticker))
            tasks = [asyncio.create_task(ws.connect()) for ws in async_sockets]

        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout)
        except TimeoutError:
            await asyncio.gather(*[ws.close_connection() for ws in async_sockets])
            for task in tasks:
                task.cancel()

        results = await asyncio.gather(*[ws.get_data() for ws in async_sockets])
        update_ids, client_timestamps, delays = list(), list(), list()

        for ws_result in results:
            update_ids.append(ws_result[0])
            client_timestamps.append(ws_result[1])
            delays.append(ws_result[2])

        return update_ids, client_timestamps, delays

    return asyncio.run(runner())


def run_SWST(ticker: str, timeout: int, num_subs: int) -> Tuple[List[List[int]], ...]:
    """
    Run single websockets via single threads. All subscriptions will be made via single websocket,
    which will recive data asyncronously. Each coroutione has his own id, and returns hiw own result data.

    :param ticker: future's ticker
    :type ticker: str
    :param timeout: lifetime in seconds of each connection
    :type timeout: int
    :param num_subs: number of coroutines
    :type num_subs: int
    :return Tuple[List[List[int]], ...]: list of update ids, client timestamps and delays for each connection
    """

    async def runner():
        async_socket = AsyncWSv2(ProjectConstants.BINANCE_FUTURES_WS, ticker, num_subs)
        task = asyncio.create_task(async_socket.make_multiple_subscriptions())
        try:
            await asyncio.wait_for(task, timeout=timeout)
        except TimeoutError:
            task.cancel()
            return await asyncio.create_task(async_socket.get_data())

    return asyncio.run(runner())
