import json
import asyncio
import websockets
from binance import AsyncClient, BinanceSocketManager


# ***************************************************************************************************************


# async def main():
#     client = await AsyncClient.create()
#     # res = await client.futures_exchange_info()
#     # print(json.dumps(res, indent=2))
#     bsm = BinanceSocketManager(client)
#     futures = ['btcusdt@bookTicker', 'btcusdt@bookTicker']
#
#     async with bsm.multiplex_socket(futures) as stream:
#         while True:
#             msg = await stream.recv()
#             print(msg)
#             print("***"*50)
#
# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())

# ***************************************************************************************************************


# async def run_it(i):
#     client = await AsyncClient.create()
#     bsm = BinanceSocketManager(client)
#
#     async with bsm.futures_depth_socket('btcusdt') as stream:
#         while True:
#             print(i)
#             msg = await stream.recv()
#             print(msg)
#             print("***"*50)
#
#
# async def main():
#     all_runs = [run_it(i) for i in range(2)]
#     await asyncio.gather(*all_runs)
#
#
# asyncio.run(main())

# ***************************************************************************************************************


async def candle_stick_data():
    url = "wss://fstream.binance.com/ws"
    ws = websockets.connect(url)
    async with ws as sock:
        check_combined = json.dumps({"method": "SET_PROPERTY", "params": ["combined", True], "id": 4})
        pairs1 = json.dumps({"method": "SUBSCRIBE", "params": ["btcusdt@bookTicker", "btcusdt@bookTicker"], "id": 1})
        pairs2 = json.dumps({"method": "SUBSCRIBE", "params": ["btcusdt@bookTicker"], "id": 2})
        await sock.send(check_combined)
        await sock.send(pairs1)
        await sock.send(pairs2)
        while True:
            resp = await sock.recv()
            print(f"< {resp}")
            print("***" * 50)

asyncio.get_event_loop().run_until_complete(candle_stick_data())
