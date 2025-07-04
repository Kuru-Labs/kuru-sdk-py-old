import re
import asyncio

error_codes = {
    "bb55fd27": "Insufficient Liquidity",
    "ff633a38": "Length Mismatch", 
    "fd993161": "Insufficient Native Asset",
    "ead59376": "Native Asset Not Required",
    "70d7ec56": "Native Asset Transfer Failed",
    "829f7240": "Order Already Filled Or Cancelled",
    "06e6da4d": "Post Only Error",
    "91f53656": "Price Error",
    "0a5c4f1f": "Size Error",
    "8199f5f3": "Slippage Exceeded",
    "272d3bf7": "Tick Size Error",
    "0b252431": "Too Much Size Filled",
    "7939f424": "Transfer From Failed",
    "f4d678b8": "Insufficient Balance",
    "cd41a9e3": "Native Asset Mismatch",
    "e84c4d58": "Only Router Allowed",
    "e8430787": "Only Verified Markets Allowed",
    "8579befe": "Zero Address Not Allowed",
    "130e7978": "Base And Quote Asset Same",
    "9db8d5b1": "Invalid Market",
    "d09b273e": "No Markets Passed",
    "d226f9d4": "Insufficient Liquidity Minted",
    "b9873846": "Insufficient Quote Token",
    "6a2628d9": "New Size Exceeds Partially Filled Size"
}

def get_error_message(error: str | tuple) -> str:
    """
    Parse error code and return corresponding error message.
    Handles both string error codes and tuple error codes like ('0x91f53656', '0x91f53656')
    """
    
    # Handle tuple error format
    if isinstance(error, tuple):
        error = error[0]  # Take first element of tuple
    else:
        # Use regex to extract error code by removing parentheses, quotes and taking first item before comma
        error = re.sub(r"[()'\s]", "", error).split(',')[0]
    # Remove '0x' prefix if present
    error = error.replace('0x', '')
    
    return error_codes.get(error, f"Unknown error: {error}")

async def maybe_await(value):
    """Return awaited result if *value* is awaitable, otherwise return it untouched."""
    if asyncio.iscoroutine(value):
        return await value
    return value

__all__ = [
    'get_error_message',
    'maybe_await',
]
