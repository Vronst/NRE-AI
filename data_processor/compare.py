"""Module contains tools to compare different things."""


def commodieties_diff(first: dict, second: dict) -> dict:
    """Compares two dicts and returns diff.

    Args:
        first: dict with commodieties.
        second: dict with commodieties.

    Returns:
        dict: diff between first and second.
    """
    result: dict = {}
    # print(first, second, sep='\n\n')
    for key, value in first.items():
        # print(key, value, sep='\n', end='\n\n')
        other_val = second[key]
        if value is None:
            if other_val is not None:
                result[key] = other_val
            continue
        elif other_val is None:
            result[key] = None
            continue

        # metal {...}
        oth_value = second[key]
        quantity = oth_value["quantity"] - value["quantity"]

        # we take oth_value price since, we are changing it
        # based on reg_price (from value)
        # the reg_price is static and price should be fluid
        # same with quantity
        price = oth_value["price"] - value["price"]
        reg_price = value["regular_price"]
        reg_quantity = value["regular_quantity"]

        result[key] = {
            "quantity_diff": quantity,
            "price_diff": price,
            "reg_price": reg_price,
            "reg_quantity": reg_quantity,
        }

    return result
