import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from kuru_sdk.websocket_handler import WebSocketHandler


from kuru_sdk.types import OrderCancelledPayload, OrderCreatedPayload, OrderRequest, TradePayload

from kuru_sdk.client_order_executor import ClientOrderExecutor

from web3 import AsyncWeb3, AsyncHTTPProvider
from kuru_sdk import Orderbook, TxOptions
import os
import json
import argparse
import asyncio
from dotenv import load_dotenv
import signal

load_dotenv()

# Network and contract configuration
NETWORK_RPC = os.getenv("RPC_URL") 

print(f"NETWORK_RPC: {NETWORK_RPC}")

ADDRESSES = {
    'margin_account': '0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef',
    'orderbook': '0x05e6f736b5dedd60693fa806ce353156a1b73cf3',
    'chog': '0x7E9953A11E606187be268C3A6Ba5f36635149C81',
    'mon': '0x0000000000000000000000000000000000000000'
}


    
class OrderExecutor:
    def __init__(self):
        self.client = None
        self.shutdown_event = None

        self.cloid_to_order = {}
        self.order_id_to_cloid = {}  
        self.cloid_status = {}

    def on_order_created(self, payload: OrderCreatedPayload):
        print(f"Order created: {payload}")
        cloid = self.client.order_id_to_cloid[payload.order_id]
        if cloid:
            self.client.cloid_to_order[cloid].size = payload.remaining_size
            self.client.cloid_to_order[cloid].is_cancelled = payload.is_canceled
            if payload.is_canceled:
                self.cloid_status[cloid] = "cancelled"
            elif payload.remaining_size == 0:
                self.cloid_status[cloid] = "filled"
            else:
                self.cloid_status[cloid] = "active"
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print(self.client.cloid_to_order[cloid])
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    
    def on_trade(self, payload: TradePayload):
        print(f"Trade: {payload}")
        order_id = payload.order_id
        cloid = self.client.order_id_to_cloid[order_id]
        if cloid:
            self.client.cloid_to_order[cloid].size = payload.updated_size
            if payload.updated_size == 0:
                self.cloid_status[cloid] = "filled"
            else:
                self.cloid_status[cloid] = "partially_filled"
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print(self.client.cloid_to_order[cloid])
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    
    def on_order_cancelled(self, payload: OrderCancelledPayload):
        print(f"Order cancelled: {payload}")
        for order_id in payload.order_ids:
            cloid = self.client.order_id_to_cloid[order_id]
            if cloid:
                self.client.cloid_to_order[cloid].is_cancelled = True
                self.cloid_status[cloid] = "cancelled"
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        print(self.client.cloid_to_order[cloid])
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    async def initialize(self):
        self.shutdown_event = asyncio.Future()
        
        self.client = ClientOrderExecutor(
            web3=AsyncWeb3(AsyncHTTPProvider(NETWORK_RPC)),
            contract_address=ADDRESSES['orderbook'],
            private_key=os.getenv("PK"),
        )

        ws_url = f"wss://ws.testnet.kuru.io"

        self.ws_client = WebSocketHandler(
            websocket_url=ws_url,
            market_address=ADDRESSES['orderbook'],
            market_params=self.client.orderbook.market_params,
            on_order_created=self.on_order_created,
            on_trade=self.on_trade,
            on_order_cancelled=self.on_order_cancelled
        )

        await self.ws_client.connect()
        
        # Add signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.shutdown(s)))

    async def shutdown(self, sig):
        print(f"\nReceived exit signal {sig.name}...")
        print("Disconnecting client...")
        try:
            await self.ws_client.disconnect()
        except Exception as e:
            print(f"Error during disconnect: {e}")
        finally:
            print("Client disconnected.")
            self.shutdown_event.set_result(True)
            # Optional: Clean up signal handlers
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.remove_signal_handler(sig)

    async def place_batch_orders(self):
        orders = [
            OrderRequest(
                market_address=ADDRESSES['orderbook'],
                order_type='limit',
                side='buy',
                price=0.0000002,
                size=10000,
                cloid="mm_1"
            ),
            OrderRequest(
                market_address=ADDRESSES['orderbook'],
                order_type='limit',
                side='buy',
                price=0.0000003,
                size=10000,
                cloid="mm_2"
            ),
            # OrderRequest(
            #     market_address=ADDRESSES['orderbook'],
            #     order_type='limit',
            #     side='sell',
            #     price=0.0002,
            #     size=10000,
            #     cloid="mm_3"
            #   ),
        ]

        for order in orders:
            if order.cloid:
                self.client.cloid_to_order[order.cloid] = order
        
        tx_hash = await self.client.batch_orders(orders)
        print(f"Batch order transaction hash: {tx_hash}")

    async def place_and_cancel_orders(self):
        new_orders = [
            OrderRequest(
                market_address=ADDRESSES['orderbook'],
                order_type='limit',
                side='buy',
                price=0.0000004,
                size=10000,
                cloid="mm_4"
            ),
            # OrderRequest(
            #     market_address=ADDRESSES['orderbook'],
            #     order_type='limit',
            #     side='sell',
            #     price=0.0002,
            #     size=10000,
            #     cloid="mm_5"
            # ),
            OrderRequest(
                market_address=ADDRESSES['orderbook'],
                order_type='cancel',
                cancel_cloids=["mm_1", "mm_2"]
            )
        ]

        for order in new_orders:
            if order.cloid:
                self.client.cloid_to_order[order.cloid] = order

        tx_hash = await self.client.batch_orders(new_orders)
        print(f"Batch order transaction hash: {tx_hash}")

    async def run(self):
        try:
            await self.initialize()
            # Place initial batch orders
            await self.place_batch_orders()

            await asyncio.sleep(3)

            # Place new orders and cancel existing ones
            await self.place_and_cancel_orders()

            print("Order placed. Running indefinitely. Press Ctrl+C to exit.")
            await self.shutdown_event  # Wait until shutdown signal is received
        
        except asyncio.CancelledError:
            print("Main task cancelled.")
        finally:
            # Ensure disconnect is called even if there's an error before shutdown_event is awaited
            if self.shutdown_event and not self.shutdown_event.done():
                print("Performing cleanup due to unexpected exit...")
                # await self.ws_client.disconnect()
                print("Client disconnected.")

async def main():
    executor = OrderExecutor()
    await executor.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt caught in __main__. Exiting gracefully...")
