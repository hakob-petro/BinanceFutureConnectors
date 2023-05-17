# -*- coding: utf-8 -*-

# Standard modules
import os
import argparse

# Third-party modules
import pandas as pd

# Project modules
from constants import ProjectConstants
from binance_logger import init_logger
from runner import run_SWST, run_MWST, run_MWMT


def get_args():
    parser = argparse.ArgumentParser(prog="Binance usdt margin futures market connector.",
                                     description="This program connects to Binance futures market via api "
                                                 "and gets data of certain ticker.",
                                     usage='python main.py [options] arguments')

    parser.add_argument("-f", "--future", metavar="future", type=str, required=True, dest="future",
                        help="""Specify future's ticker. Example: btcusdt.\n""")
    parser.add_argument("-n", "--number_of_connection", metavar="conn_num", type=int, required=False, dest="conn_num",
                        default=1, help=f"""Specify number of concurrent connections. Default value 1.\n""")
    parser.add_argument("-t", "--timeout", metavar="timeout", type=int, required=False, dest="timeout",
                        default=60, help=f"""Specify timeout in seconds for each connection. Default 60.\n""")
    parser.add_argument("-m", "--method", metavar="method", type=str, required=True, dest="method",
                        default="MWMT", help=f"""Specify which method to use for connection.\n Available methods: 
                        MWMT [multiple websockets, multiple threads], MWST [multiple websockets, single thread], 
                        SWST [single websocket, single thread]
                        """)
    return parser.parse_args()


if __name__ == "__main__":
    args = vars(get_args())
    init_logger()

    update_ids_l, client_timestamps_l, delays_l = None, None, None
    if args["method"] == "MWMT":
        update_ids_l, client_timestamps_l, delays_l = run_MWMT(args["future"], args["timeout"], args["conn_num"])
        save_dir = os.path.join(ProjectConstants.DATA_DIR, "MWMT")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    elif args["method"] == "MWST":
        update_ids_l, client_timestamps_l, delays_l = run_MWST(args["future"], args["timeout"], args["conn_num"])
        save_dir = os.path.join(ProjectConstants.DATA_DIR, "MWST")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    elif args["method"] == "SWST":
        update_ids_l, client_timestamps_l, delays_l = run_SWST(args["future"], args["timeout"], args["conn_num"])
        save_dir = os.path.join(ProjectConstants.DATA_DIR, "SWST")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    # Saving data
    for i, (update_ids, client_timestamps, delays) in enumerate(zip(update_ids_l, client_timestamps_l, delays_l)):
        df = pd.DataFrame(list(zip(update_ids, client_timestamps, delays)),
                          columns=["update_id", "client_timestamps", "delay"])
        pth = os.path.join(save_dir, f"connection_{i}.pkl")
        df.to_pickle(pth)
        print(f"Data of connection {i} had been saved at {pth}")
