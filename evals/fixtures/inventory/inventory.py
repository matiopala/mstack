def reserve(stock, requested):
    """Reserve nonnegative integer quantities from a local stock dictionary."""
    for sku, quantity in requested:
        if stock.get(sku, 0) < quantity:
            raise ValueError(f"Insufficient stock: {sku}")
        stock[sku] = stock.get(sku, 0) - quantity
    return stock
