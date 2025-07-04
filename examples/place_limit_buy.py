import sys
from pathlib import Path
import os
import asyncio
from dotenv import load_dotenv
from web3 import AsyncWeb3, AsyncHTTPProvider

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from kuru_sdk.client_order_executor import ClientOrderExecutor
from kuru_sdk.types import OrderRequest, TxOptions

load_dotenv()

NETWORK_RPC = os.getenv("RPC_URL")  
PRIVATE_KEY = os.getenv("PK")  
ORDERBOOK_ADDRESS = "0x05e6f736b5dedd60693fa806ce353156a1b73cf3"

# --- Order Details ---
# Define the details of the limit buy order you want to place
LIMIT_PRICE = 0.0001  # Price per unit
ORDER_SIZE = 10000  # Number of units to buy
CLIENT_ORDER_ID = "cloid_1" # A unique identifier for your order
POST_ONLY = False # If True, the order will only be added to the book and not match existing orders

async def place_single_limit_buy(client: ClientOrderExecutor):
    """Place a single limit buy order using the configured client."""

    print(f"Attempting to place limit buy order:")
    print(f"  Client Order ID: {CLIENT_ORDER_ID}")
    print(f"  Price: {LIMIT_PRICE}")
    print(f"  Size: {ORDER_SIZE}")
    print(f"  Post Only: {POST_ONLY}")

    # Create the order request object
    order = OrderRequest(
        market_address=ORDERBOOK_ADDRESS,
        order_type='limit',
        side='buy',
        price=str(LIMIT_PRICE),
        size=str(ORDER_SIZE),
        post_only=POST_ONLY,
        cloid=CLIENT_ORDER_ID
    )

    try:
        tx_hash = await client.place_order(order)
        print(f"Successfully placed order. Transaction Hash: {tx_hash}")
        return tx_hash
    except Exception as e:
        print(f"Error placing limit buy order: {str(e)}")
        return None

async def main():
    if not NETWORK_RPC or not PRIVATE_KEY or not ORDERBOOK_ADDRESS:
        print("Error: Please set RPC_URL, PK, and ORDERBOOK_ADDRESS environment variables or update the script.")
        return

    web3_instance = AsyncWeb3(AsyncHTTPProvider(NETWORK_RPC))
    client = ClientOrderExecutor(
        web3=web3_instance,
        contract_address=ORDERBOOK_ADDRESS,
        private_key=PRIVATE_KEY,
    )

    print(f"Using Orderbook at address: {ORDERBOOK_ADDRESS}")
    print(f"Using wallet address: {client.wallet_address}")

    # Place the order
    await place_single_limit_buy(client)



if __name__ == "__main__":
    asyncio.run(main())
