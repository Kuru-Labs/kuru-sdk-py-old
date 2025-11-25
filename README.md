# Kuru Python SDK

A Python SDK for interacting with the Kuru protocol, enabling market makers to manage orders, interact with margin accounts, and query exchange data.


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

This SDK provides tools to interact with the Kuru order book and margin accounts primarily through Web3 for real-time order execution. It also offers a basic REST API client for querying data.

### Prerequisites

*   Python 3.8+
*   A Monad RPC URL (e.g., from Infura, Alchemy, or a local node)
*   A private key for the wallet interacting with the Kuru contracts.

### Configuration

The SDK often requires environment variables for configuration. Create a `.env` file in your project root:

```dotenv
RPC_URL=YOUR_ETHEREUM_RPC_URL
PK=YOUR_WALLET_PRIVATE_KEY
// Optional: WebSocket URL if you implement your own
// streaming client against the Kuru WebSocket API.
// WEBSOCKET_URL=wss://ws.testnet.kuru.io
```

### Basic Usage: Placing Orders

Here's a simplified example of placing a batch of orders using the `ClientOrderExecutor`:

```python
import asyncio
import os
from web3 import Web3
from dotenv import load_dotenv
from kuru_sdk import ClientOrderExecutor
from kuru_sdk.types import OrderRequest

load_dotenv()

# Network and contract configuration (replace with actual addresses)
NETWORK_RPC = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PK")
ORDERBOOK_ADDRESS = '0x05e6f736b5dedd60693fa806ce353156a1b73cf3' # Example address

async def run():
    client = ClientOrderExecutor(
        web3=Web3(Web3.HTTPProvider(NETWORK_RPC)),
        contract_address=ORDERBOOK_ADDRESS,
        private_key=PRIVATE_KEY,
    )

    try:
        print("Connecting client...")
        await client.connect()
        print("Client connected.")

        # Define orders
        orders_to_place = [
            OrderRequest(
                market_address=ORDERBOOK_ADDRESS,
                order_type='limit',
                side='buy',
                price=0.0000002,
                size=10000,
                cloid="my_buy_order_1" # Unique client order ID
            ),
            OrderRequest(
                market_address=ORDERBOOK_ADDRESS,
                order_type='limit',
                side='sell',
                price=0.0000005,
                size=5000,
                cloid="my_sell_order_1"
            ),
        ]

        # Place batch orders
        tx_hash_place = await client.batch_orders(orders_to_place)
        print(f"Batch place order transaction hash: {tx_hash_place}")

        await asyncio.sleep(5) # Allow time for processing

        # Define cancellations
        orders_to_cancel = [
             OrderRequest(
                market_address=ORDERBOOK_ADDRESS,
                order_type='cancel',
                cancel_cloids=["my_buy_order_1"] # Reference by client order ID
            )
        ]

        # Cancel orders
        tx_hash_cancel = await client.batch_orders(orders_to_cancel)
        print(f"Batch cancel order transaction hash: {tx_hash_cancel}")

        # Keep running or add other logic here
        print("Orders managed. Add further logic or close.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Finished example run.")

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nExiting gracefully...")

```

## Key Features

*   **`ClientOrderExecutor`**: Manages Orders with client orders for real-time order placement, cancellation, and updates. Uses Web3 for signing and sending transactions.
*   **`Orderbook`**: Interacts directly with the Orderbook contract via Web3 calls (primarily for read operations or direct transactions if not using the WebSocket client).
*   **`MarginAccount`**: Interacts with the MarginAccount contract via Web3 calls.
*   **`KuruAPI`**: A simple client for querying REST API endpoints (e.g., fetching user orders, trades).
*   **`types`**: Defines data structures like `OrderRequest` for standardized interactions.
*   **`websocket_handler`**: (Deprecated and removed) Previously provided WebSocket streaming helpers; users should now implement their own streaming client if needed.

## Examples

The `examples/` directory contains more detailed scripts demonstrating various functionalities:

*   `deposit.py`: Shows how to deposit funds into the margin account.
*   `place_order.py`: Demonstrates placing and cancelling orders via WebSocket, including signal handling for graceful shutdown.
*   `simple_market_maker.py`: A more complex example implementing a basic market-making strategy.
*   `view_orderbook.py`: Example of querying order book data.
*   `ws_place_order.py`: Another example focusing on WebSocket order placement.
