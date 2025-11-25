import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from web3 import Web3
from kuru_sdk import MONAD_MAINNET, NetworkConfig
from kuru_sdk.config import create_margin_account
import os

from dotenv import load_dotenv

load_dotenv()

# Network configuration (use env RPC_URL if provided, otherwise default)
NETWORK_CONFIG = NetworkConfig(
    rpc_url=os.getenv("RPC_URL", MONAD_MAINNET.rpc_url),
    websocket_url=None,
    chain_id=MONAD_MAINNET.chain_id,
    margin_contract_address=MONAD_MAINNET.margin_contract_address,
    common_tokens=MONAD_MAINNET.common_tokens,
)

async def main():
    web3 = Web3(Web3.HTTPProvider(NETWORK_CONFIG.rpc_url))
    margin_account = create_margin_account(
        private_key=os.getenv('PK'),
        config=NETWORK_CONFIG,
    )

    wallet_address = margin_account.wallet_address

    # Example: deposit MON using configured token address
    mon_address = NETWORK_CONFIG.common_tokens["MON"]["address"]

    await margin_account.deposit(
        token=mon_address,
        amount=100000000000000000000000
    )

    balance = await margin_account.get_balance(
        user_address=wallet_address,
        token=mon_address,
    )
    print(f"Balance: {balance}")
    

if __name__ == "__main__":
    asyncio.run(main())
