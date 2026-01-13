def short_number(n):
    if n is None:
        return "0"

    n = float(n)

    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B".rstrip("0").rstrip(".")
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".rstrip("0").rstrip(".")
    if n >= 1_000:
        return f"{n:,.0f}"
    return f"{int(n)}"
