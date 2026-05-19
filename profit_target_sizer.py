import argparse
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class SizingInputs:
    entry_price: float
    exit_price: float
    realized_profit: float
    current_volume: float
    target_profits: list[float]
    order_type: str = 'buy'
    stop_loss_price: Optional[float] = None
    account_balance: Optional[float] = None


@dataclass
class ProfitTargetPlan:
    target_profit: float
    required_volume: float
    volume_multiple: float
    estimated_loss_at_stop: Optional[float]
    estimated_risk_percent: Optional[float]


def _validate_inputs(inputs: SizingInputs) -> None:
    if inputs.entry_price <= 0:
        raise ValueError('entry_price must be greater than 0')
    if inputs.exit_price <= 0:
        raise ValueError('exit_price must be greater than 0')
    if inputs.current_volume <= 0:
        raise ValueError('current_volume must be greater than 0')
    if inputs.realized_profit <= 0:
        raise ValueError('realized_profit must be greater than 0')
    if not inputs.target_profits:
        raise ValueError('at least one target profit is required')
    if any(target <= 0 for target in inputs.target_profits):
        raise ValueError('target profits must all be greater than 0')


def _absolute_price_move(entry_price: float, exit_price: float) -> float:
    move = abs(exit_price - entry_price)
    if move <= 0:
        raise ValueError('entry_price and exit_price must differ to infer profit scaling')
    return move


def _profit_per_volume_unit(realized_profit: float, current_volume: float) -> float:
    return realized_profit / current_volume


def _profit_per_volume_per_price_unit(
    realized_profit: float,
    current_volume: float,
    entry_price: float,
    exit_price: float,
) -> float:
    return realized_profit / (current_volume * _absolute_price_move(entry_price, exit_price))


def build_profit_target_plan(inputs: SizingInputs) -> list[ProfitTargetPlan]:
    _validate_inputs(inputs)

    profit_per_volume = _profit_per_volume_unit(inputs.realized_profit, inputs.current_volume)
    price_profit_rate = _profit_per_volume_per_price_unit(
        inputs.realized_profit,
        inputs.current_volume,
        inputs.entry_price,
        inputs.exit_price,
    )

    estimated_loss_per_volume = None
    if inputs.stop_loss_price is not None and inputs.stop_loss_price > 0:
        stop_distance = abs(inputs.entry_price - inputs.stop_loss_price)
        estimated_loss_per_volume = price_profit_rate * stop_distance

    plans: list[ProfitTargetPlan] = []
    for target_profit in inputs.target_profits:
        required_volume = target_profit / profit_per_volume
        estimated_loss_at_stop = None
        estimated_risk_percent = None

        if estimated_loss_per_volume is not None:
            estimated_loss_at_stop = required_volume * estimated_loss_per_volume
            if inputs.account_balance and inputs.account_balance > 0:
                estimated_risk_percent = (estimated_loss_at_stop / inputs.account_balance) * 100.0

        plans.append(
            ProfitTargetPlan(
                target_profit=target_profit,
                required_volume=required_volume,
                volume_multiple=required_volume / inputs.current_volume,
                estimated_loss_at_stop=estimated_loss_at_stop,
                estimated_risk_percent=estimated_risk_percent,
            )
        )

    return plans


def _format_money(value: Optional[float], currency: str) -> str:
    if value is None:
        return '-'
    return f'{currency}{value:,.2f}'


def _format_percent(value: Optional[float]) -> str:
    if value is None:
        return '-'
    return f'{value:.2f}%'


def render_report(inputs: SizingInputs, plans: Iterable[ProfitTargetPlan], currency: str) -> str:
    price_move = _absolute_price_move(inputs.entry_price, inputs.exit_price)
    profit_per_volume = _profit_per_volume_unit(inputs.realized_profit, inputs.current_volume)
    price_profit_rate = _profit_per_volume_per_price_unit(
        inputs.realized_profit,
        inputs.current_volume,
        inputs.entry_price,
        inputs.exit_price,
    )

    lines = [
        'Observed trade baseline',
        f'  Order type: {inputs.order_type.upper()}',
        f'  Entry price: {inputs.entry_price:,.2f}',
        f'  Exit/current price: {inputs.exit_price:,.2f}',
        f'  Price move used for calibration: {price_move:,.2f}',
        f'  Realized profit: {_format_money(inputs.realized_profit, currency)}',
        f'  Current volume: {inputs.current_volume:,.4f}',
        f'  Profit per 1.00 volume on same move: {_format_money(profit_per_volume, currency)}',
        f'  Profit per 1.00 volume per 1.00 price unit: {_format_money(price_profit_rate, currency)}',
        '',
        'Required size for target profits',
    ]

    for plan in plans:
        lines.append(
            f'  Target {_format_money(plan.target_profit, currency)} -> '
            f'volume {plan.required_volume:,.4f} '
            f'({plan.volume_multiple:.2f}x current), '
            f'est. stop loss {_format_money(plan.estimated_loss_at_stop, currency)}, '
            f'est. balance risk {_format_percent(plan.estimated_risk_percent)}'
        )

    if inputs.stop_loss_price is not None:
        lines.extend([
            '',
            'Stop-loss check',
            f'  Stop-loss price: {inputs.stop_loss_price:,.2f}',
            f'  Stop distance from entry: {abs(inputs.entry_price - inputs.stop_loss_price):,.2f}',
        ])

    return '\n'.join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Backsolve the volume needed to reach target profit amounts from an observed trade result.'
    )
    parser.add_argument('--entry-price', type=float, required=True)
    parser.add_argument('--exit-price', type=float, required=True)
    parser.add_argument('--realized-profit', type=float, required=True)
    parser.add_argument('--current-volume', type=float, required=True)
    parser.add_argument('--target-profit', type=float, nargs='+', required=True)
    parser.add_argument('--order-type', default='buy', choices=['buy', 'sell'])
    parser.add_argument('--stop-loss-price', type=float)
    parser.add_argument('--account-balance', type=float)
    parser.add_argument('--currency', default='R')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inputs = SizingInputs(
        entry_price=args.entry_price,
        exit_price=args.exit_price,
        realized_profit=args.realized_profit,
        current_volume=args.current_volume,
        target_profits=list(args.target_profit),
        order_type=args.order_type,
        stop_loss_price=args.stop_loss_price,
        account_balance=args.account_balance,
    )
    plans = build_profit_target_plan(inputs)
    print(render_report(inputs, plans, args.currency))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())