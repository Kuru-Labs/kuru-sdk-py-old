from dataclasses import dataclass
from typing import Optional

from web3 import Web3

from .client_order_executor import ClientOrderExecutor


@dataclass
class NetworkConfig:
    """Simple network configuration for Kuru SDK clients."""

    rpc_url: str
    websocket_url: Optional[str] = None
    chain_id: Optional[int] = None


# Monad mainnet defaults
MONAD_MAINNET_CHAIN_ID = 143

MONAD_MAINNET = NetworkConfig(
    rpc_url="https://rpc.monad.xyz",
    websocket_url="wss://rpc.monad.xyz",
    chain_id=MONAD_MAINNET_CHAIN_ID,
)


def create_client_order_executor(
    orderbook_address: str,
    private_key: str,
    config: NetworkConfig = MONAD_MAINNET,
    kuru_api_url: Optional[str] = None,
    logger=True,
) -> ClientOrderExecutor:
    """Create a ``ClientOrderExecutor`` from a network config.

    By default, this uses ``MONAD_MAINNET``. You can provide a custom
    ``NetworkConfig`` to target other networks or RPC providers.
    """

    web3 = Web3(Web3.HTTPProvider(config.rpc_url))

    return ClientOrderExecutor(
        web3=web3,
        contract_address=orderbook_address,
        private_key=private_key,
        kuru_api_url=kuru_api_url,
        logger=logger,
    )


__all__ = [
    "NetworkConfig",
    "MONAD_MAINNET_CHAIN_ID",
    "MONAD_MAINNET",
    "create_client_order_executor",
]

