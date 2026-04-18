"""
Tool 3: calculate_impermanent_loss
Pure math tool — always free, no API needed.
"""
from ..calculations import calculate_impermanent_loss as calc_il


async def calculate_il_impl(
    token_a_price_change: float,
    token_b_price_change: float,
    investment_amount: float = 10_000,
) -> dict:
    """
    Calculate exact impermanent loss for a 50/50 LP pair.

    Args:
        token_a_price_change: % change for token A (e.g., 50 = +50%)
        token_b_price_change: % change for token B (e.g., -20 = -20%)
        investment_amount: Initial investment in USD

    Returns:
        IL details, hold vs LP, net at various fee APYs.
    """
    return calc_il(token_a_price_change, token_b_price_change, investment_amount)
