from decimal import Decimal, getcontext

from pint import UnitRegistry

ureg = UnitRegistry()
ureg.define("dozen = 12 * count")
ureg.define("each = 1 * count")
getcontext().prec = 6


def to_canonical(qty: float | str, unit: str, density: float | None = None):
    """
    qty, unit -> (Decimal value, canonical_unit)
    If density supplied (g / mL) allows volume<->mass conversion.
    """
    q = Decimal(str(qty)) * ureg(unit)

    if density and q.u in (ureg.liter, ureg.milliliter):
        with ureg.context("density"):
            ureg.define(f"density = {density} gram / milliliter")
    base = q.to_base_units()
    val = Decimal(str(base.magnitude)).quantize(Decimal("0.001"))
    return val, str(base.units)
