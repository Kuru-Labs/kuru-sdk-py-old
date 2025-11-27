import asyncio
import sys
from pathlib import Path


# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from kuru_sdk.client_order_executor import ClientOrderExecutor
from kuru_sdk import MONAD_MAINNET, NetworkConfig

from web3 import Web3
import os

from dotenv import load_dotenv

load_dotenv()

# Network configuration (use env RPC_URL if provided, otherwise default)
NETWORK_CONFIG = NetworkConfig(
    rpc_url=os.getenv("RPC_URL", MONAD_MAINNET.rpc_url),
    websocket_url=None,
    chain_id=MONAD_MAINNET.chain_id,
)

async def main():
    web3 = Web3(Web3.HTTPProvider(NETWORK_CONFIG.rpc_url))

    # Example orderbook address (kept explicit here)
    orderbook_address = '0xd3af145f1aa1a471b5f0f62c52cf8fcdc9ab55d3'

    client = ClientOrderExecutor(
        web3=web3,
        contract_address=orderbook_address,
        private_key=os.getenv('PK')
    )

    orderbook = await client.get_l2_book()
    print(orderbook)
    
    
if __name__ == "__main__":
    asyncio.run(main())
