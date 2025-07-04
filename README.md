# Kuru Python SDK

A Python SDK for interacting with the Kuru protocol, enabling market makers to manage orders, interact with margin accounts, and query exchange data.

⚠️ **Important:** As of v0.2.0, the SDK now uses `AsyncWeb3` for all state-changing (non-view) contract interactions such as order placement and margin deposit/withdraw transactions. Regular synchronous `Web3` **can still be used for pure read calls** (e.g. checking on-chain balances) but any examples that send transactions must construct an `AsyncWeb3` instance.

## Create a venv

```
python -m venv kuru-venv
```

## Installation

To install the Kuru SDK, you can use pip:

```bash
pip install kuru-sdk
```


## Getting Started

This SDK provides tools to interact with the Kuru order book and margin accounts primarily through Web3 and WebSocket connections for real-time order execution. It also offers a basic REST API client for querying data.

### Prerequisites

*   Python 3.8+
*   A Monad RPC URL (e.g., from Infura, Alchemy, or a local node)
*   A private key for the wallet interacting with the Kuru contracts.

### Configuration

The SDK often requires environment variables for configuration. Create a `.env` file in your project root:

```dotenv
RPC_URL=YOUR_ETHEREUM_RPC_URL
PK=YOUR_WALLET_PRIVATE_KEY
# Optional: WebSocket URL if different from default
WEBSOCKET_URL=wss://ws.testnet.kuru.io
```

### Basic Usage: Placing Orders

Below is a simplified **async** example that connects to the Kuru WebSocket and places a batch of orders via `ClientOrderExecutor`.

> **Why AsyncWeb3?**  
> All write-operations (order placement, deposits, withdrawals, approvals, etc.) must now be executed through `AsyncWeb3`.  Read-only calls may still use regular `Web3`.

```python
import asyncio
import os
from dotenv import load_dotenv
from web3 import AsyncWeb3, AsyncHTTPProvider

from kuru_sdk.client_order_executor import ClientOrderExecutor
from kuru_sdk.types import OrderRequest

load_dotenv()

RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PK")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "wss://ws.testnet.kuru.io")
ORDERBOOK_ADDRESS = "0x05e6f736b5dedd60693fa806ce353156a1b73cf3"


async def main():
    # 1. Create an AsyncWeb3 instance – this is mandatory for any state-changing tx.
    web3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))

    # 2. Initialise the ClientOrderExecutor with that AsyncWeb3 instance
    client = ClientOrderExecutor(
        web3=web3,
        contract_address=ORDERBOOK_ADDRESS,
        private_key=PRIVATE_KEY,
    )

    # 3. Define limit orders to batch place
    orders_to_place = [
        OrderRequest(
            market_address=ORDERBOOK_ADDRESS,
            order_type="limit",
            side="buy",
            price="0.0000002",
            size="10000",
            cloid="my_buy_order_1",
        ),
        OrderRequest(
            market_address=ORDERBOOK_ADDRESS,
            order_type="limit",
            side="sell",
            price="0.0000005",
            size="5000",
            cloid="my_sell_order_1",
        ),
    ]

    try:
        tx_hash = await client.batch_orders(orders_to_place)
        print("Batch place order tx_hash:", tx_hash)

        # wait a bit for on-chain inclusion (or subscribe via WebSocket)
        await asyncio.sleep(5)

    finally:
        # Always close underlying connections cleanly
        await web3.provider.coro_disconnect()


if __name__ == "__main__":
    asyncio.run(main())

**Gotchya:** If you accidentally pass a synchronous `Web3` instance to `ClientOrderExecutor` or `Orderbook` for a write-operation, an explicit `TypeError` will be raised reminding you to switch to `AsyncWeb3`.

## Key Features

*   **`ClientOrderExecutor`**: Manages Orders with client orders for real-time order placement, cancellation, and updates. Uses Web3 for signing and sending transactions.
*   **`Orderbook`**: Interacts directly with the Orderbook contract via Web3 calls (primarily for read operations or direct transactions if not using the WebSocket client).
*   **`MarginAccount`**: Interacts with the MarginAccount contract via Web3 calls.
*   **`KuruAPI`**: A simple client for querying REST API endpoints (e.g., fetching user orders, trades).
*   **`types`**: Defines data structures like `OrderRequest` for standardized interactions.
*   **`websocket_handler`**: Core WebSocket communication logic used by `ClientOrderExecutor`.

## Examples

The `examples/` directory contains more detailed scripts demonstrating various functionalities:

*   `deposit.py`: Shows how to deposit funds into the margin account.
*   `place_order.py`: Demonstrates placing and cancelling orders via WebSocket, including signal handling for graceful shutdown.
*   `simple_market_maker.py`: A more complex example implementing a basic market-making strategy.
*   `view_orderbook.py`: Example of querying order book data.
*   `ws_place_order.py`: Another example focusing on WebSocket order placement.
