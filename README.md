## Install requirements

```angular2html
pip install -r requirements.txt
```

## Usage

```angular2html
usage: python main.py [options] arguments

This program connects to Binance futures market via api and gets data of certain ticker.

options:
  -h, --help            show this help message and exit
  -f future, --future future
                        Specify future's ticker. Example: btcusdt.
  -n conn_num, --number_of_connection conn_num
                        Specify number of concurrent connections. Default value 1.
  -t timeout, --timeout timeout
                        Specify timeout in seconds for each connection. Default 60.
  -m method, --method method
                        Specify which method to use for connection. Available methods: MWMT [multiple websockets, multiple threads], MWST [multiple websockets, single thread], SWST [single websocket, single thread]

```
