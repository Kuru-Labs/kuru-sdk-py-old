import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from kuru_sdk.types import OrderRequest, TxOptions
from kuru_sdk.client_order_executor import ClientOrderExecutor
from kuru_sdk.websocket_handler import WebSocketHandler
from web3 import AsyncWeb3, AsyncHTTPProvider
import os
import asyncio
from dotenv import load_dotenv
import signal
import time

load_dotenv()

# Network and contract configuration
NETWORK_RPC = os.getenv("RPC_URL")

print(f"NETWORK_RPC: {NETWORK_RPC}")

ADDRESSES = {
    'margin_account': '0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef',
    'orderbook': '0xd3af145f1aa1a471b5f0f62c52cf8fcdc9ab55d3',
    'chog': '0x7E9953A11E606187be268C3A6Ba5f36635149C81',
    'mon': '0x0000000000000000000000000000000000000000'
}


async def main():
    # Define shutdown signal
    shutdown_event = asyncio.Future()

    client = ClientOrderExecutor(
        web3=AsyncWeb3(AsyncHTTPProvider(NETWORK_RPC)),
        contract_address=ADDRESSES['orderbook'],
        private_key=os.getenv("PK"),
    )

    # Get address from private key
    account_address = client.web3.eth.account.from_key(os.getenv("PK")).address
    
    ws_url = f"wss://ws.testnet.kuru.io"
    ws_client = WebSocketHandler(
        client_order_executor=client,
        websocket_url=ws_url,
        market_address=account_address,  # Using address derived from private key
        market_params=client.orderbook.market_params,
        on_order_created=lambda payload: print(f"Order created: {payload}"),
        on_trade=lambda payload: print(f"Trade: {payload}"),
        on_order_cancelled=lambda payload: print(f"Order cancelled: {payload}"),
        logger=False
    )

    await ws_client.connect()

    async def shutdown(sig):
        print(f"\nReceived exit signal {sig.name}...")
        print("Disconnecting client...")
        try:
            # Placeholder for any cleanup tasks you may want to run before shutdown
            # (e.g. flushing logs, persisting state, etc.)
            pass
        except Exception as e:
            print(f"Error during disconnect: {e}")
        finally:
            print("Client disconnected.")
            shutdown_event.set_result(True)
            # Optional: Clean up signal handlers
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.remove_signal_handler(sig)

    # Add signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

    try:
        print("Connecting client...")
        print("Client connected.")

        # Single order
        orders = [
            OrderRequest(
                market_address=ADDRESSES['orderbook'],
                order_type='limit',
                side='sell',
                price='8',
                size='1',
                post_only=True
            )
        ]

        # Get the current nonce for the account
        current_nonce = client.web3.eth.get_transaction_count(account_address)

        tx_options = TxOptions(
            gas_limit=200_000,
            gas_price=50 * 10**9,
            max_priority_fee_per_gas=1 * 10**9,
            nonce=current_nonce
        )

        # Measure order placement time
        start_time = time.time()
        cloid = await client.place_order(orders[0], tx_options, async_execution=True)
        end_time = time.time()
        execution_time = end_time - start_time

        print(f"Order cloid: {cloid}")
        print(f"Order placement took {execution_time:.4f} seconds")

        print("Order placed. Running indefinitely. Press Ctrl+C to exit.")

        # Wait 5 seconds before checking order
        await asyncio.sleep(10)
        print(f"Exchange OrderId: {client.get_order_id_by_cloid(cloid)}")
        print(f"Order: {client.get_order_by_cloid(cloid)}")

        # Cancel order
        cancel_orders = OrderRequest(
            market_address=ADDRESSES['orderbook'],
            order_type='cancel',
            cancel_cloids=[cloid]
        )
        tx_options.nonce += 1

        start_time = time.time()
        cancel_cloids = await client.batch_orders([cancel_orders], tx_options, async_execution=True)
        end_time = time.time()
        execution_time = end_time - start_time

        print(f"Cancel Cloid: {cancel_cloids[0]}")
        print(f"Order cancellation took {execution_time:.4f} seconds")

        await asyncio.sleep(10)
        print(f"Exchange OrderId: {client.get_order_id_by_cloid(cloid)}")
        print(f"Order: {client.get_order_by_cloid(cancel_cloids[0])}")
        print(f"Limit Order: {client.get_order_by_cloid(cloid)}")
        await shutdown_event

    except asyncio.CancelledError:
        print("Main task cancelled.")
    finally:
        # Ensure disconnect is called even if there's an error before shutdown_event is awaited
        if not shutdown_event.done():
            print("Performing cleanup due to unexpected exit...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt caught in __main__. Exiting gracefully...")
