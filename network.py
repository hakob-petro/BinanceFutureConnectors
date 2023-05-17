# -*- coding: utf-8 -*-

# Standard modules
import time
import json
import _thread
import queue
import asyncio
from logging import getLogger
from typing import Tuple, List

# Third-party modules
import websocket
import websockets
from binance import AsyncClient, BinanceSocketManager

__all__ = [
    "ThreadedWS",
    "AsyncWSv1",
    "AsyncWSv2"
]


class ThreadedWS(websocket.WebSocketApp):
    def __init__(self, url, ticker: str, client_timestamp: queue.Queue, delays: queue.Queue, update_ids: queue.Queue):
        super().__init__(url, on_open=self.on_open, on_message=self.on_message,
                         on_close=self.on_close, on_error=self.on_error)
        self.url = url
        self.ticker = ticker
        self.client_timestamp = client_timestamp
        self.delays = delays
        self.update_ids = update_ids
        self.thread_id = None
        self.run_forever()

    def on_message(self, ws, message):
        curr_time = time.time_ns() // 1e6
        data = json.loads(message)
        if data is not None:
            self.update_ids.put(data["u"])
            self.delays.put(curr_time - data["E"])
            self.client_timestamp.put(curr_time)

    def on_error(self, ws, error):
        getLogger(f"{__name__}.on_close").info(f"Error occurred in socket {ws}!\n"
                                               f"Message: {error}")

    def on_close(self, ws):
        getLogger(f"{__name__}.on_close").info(f"Socket {ws} close connection!")

    def on_open(self, ws: websocket.WebSocketApp) -> None:
        def run(*args):
            # Subscribe to the ticker@bookTicker stream
            ws.send(json.dumps({"method": "SUBSCRIBE", "params": [f"{self.ticker}@bookTicker"], "id": 1}))

        getLogger(f"{__name__}.on_close").info(f"Opened websocket {ws} for connections to {self.url}!\n")
        self.thread_id = _thread.start_new_thread(run, ())
        getLogger(f"{__name__}.on_close").info(f"Starting thread {self.thread_id} for websocket {ws}"
                                               f" for connections to {self.url}!\n")


class AsyncWSv1:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.client = None
        self.socket = None
        self.client_timestamps = asyncio.Queue()
        self.delays = asyncio.Queue()
        self.update_ids = asyncio.Queue()

    async def put_data(self, data, curr_time):
        if data is not None:
            await self.update_ids.put(data["u"])
            await self.delays.put(curr_time - data["E"])
            await self.client_timestamps.put(curr_time)

    async def connect(self):
        self.client = await AsyncClient.create()
        self.socket = BinanceSocketManager(self.client)

        async with self.socket.futures_depth_socket(self.ticker) as stream:
            while True:
                message = await stream.recv()
                curr_time = time.time_ns() // 1e6
                await self.put_data(message["data"], curr_time)

    async def close_connection(self):
        await self.client.close_connection()

    @staticmethod
    async def consume_queue(q: asyncio.Queue):
        data_l = []
        while not q.empty():
            item = await q.get()
            data_l.append(item)
        return data_l

    async def get_data(self) -> Tuple[List[int], ...]:
        update_ids, client_timestamps, delays = await asyncio.gather(
            AsyncWSv1.consume_queue(self.update_ids),
            AsyncWSv1.consume_queue(self.client_timestamps),
            AsyncWSv1.consume_queue(self.delays)
        )
        return update_ids, client_timestamps, delays


class AsyncWSv2:
    def __init__(self, url, ticker, num_subs):
        self.url = url
        self.ticker = ticker
        self.num_subs = num_subs
        self.socket = websockets.connect(url)
        self.client_timestamps_l = [asyncio.Queue() for _ in range(num_subs)]
        self.delays_l = [asyncio.Queue() for _ in range(num_subs)]
        self.update_ids_l = [asyncio.Queue() for _ in range(num_subs)]

    async def put_data(self, data, curr_time, idx):
        if data is not None:
            await self.update_ids_l[idx].put(data["u"])
            await self.delays_l[idx].put(curr_time - data["E"])
            await self.client_timestamps_l[idx].put(curr_time)

    async def set_combined(self):
        set_combined = json.dumps({"method": "SET_PROPERTY", "params": ["combined", True], "id": 201})
        async with self.socket as sock:
            await sock.send(set_combined)
            return await sock.recv()

    async def get_combined(self):
        get_combined = json.dumps({"method": "GET_PROPERTY", "params": ["combined"], "id": 202})
        async with self.socket as sock:
            await sock.send(get_combined)
            return await sock.recv()

    async def subscribe(self, idx):
        sub_future = json.dumps({"method": "SUBSCRIBE", "params": [f"{self.ticker}@bookTicker"], "id": idx})
        async with self.socket as sock:
            await sock.send(sub_future)
            combined = json.loads(await self.get_combined())["result"]
            while True:
                resp = await sock.recv()
                if not combined:
                    resp = json.loads(resp)
                else:
                    resp = json.loads(resp)["data"]
                if "id" not in resp.keys():
                    curr_time = time.time_ns() // 1e6
                    await self.put_data(resp, curr_time, idx)

    async def make_multiple_subscriptions(self):
        await asyncio.gather(*[self.subscribe(idx) for idx in range(self.num_subs)])

    @staticmethod
    async def consume_queue(q: asyncio.Queue):
        data_l = []
        while not q.empty():
            item = await q.get()
            data_l.append(item)
        return data_l

    async def get_data(self) -> Tuple[List[List[int]], ...]:
        client_timestamps_l = [list() for _ in range(self.num_subs)]
        delays_l = [list() for _ in range(self.num_subs)]
        update_ids_l = [list() for _ in range(self.num_subs)]

        for idx in range(self.num_subs):
            update_ids_l[idx], client_timestamps_l[idx], delays_l[idx] = await asyncio.gather(
                AsyncWSv2.consume_queue(self.update_ids_l[idx]),
                AsyncWSv2.consume_queue(self.client_timestamps_l[idx]),
                AsyncWSv2.consume_queue(self.delays_l[idx])
            )
        return update_ids_l, client_timestamps_l, delays_l

    async def close_socket(self):
        async with self.socket as sock:
            await sock.close()
