#!/usr/bin/env python3
"""
Alpaca Markets CLI - Native HADES Tier-1 Execution Tool
Integrates with Alpaca Markets REST API v2 for trading, market data, clock, and news.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


CONFIG_PATH = os.path.expanduser("~/.config/hades/alpaca.json")


def load_config() -> Dict[str, str]:
    config: Dict[str, str] = {
        "key_id": os.environ.get("APCA_API_KEY_ID", ""),
        "secret_key": os.environ.get("APCA_API_SECRET_KEY", ""),
        "base_url": os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets"),
        "data_url": os.environ.get("APCA_API_DATA_URL", "https://data.alpaca.markets"),
    }

    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for k, v in saved.items():
                    if v and not config.get(k):
                        config[k] = str(v)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to read {CONFIG_PATH}: {e}\n")

    if not config["key_id"] or not config["secret_key"]:
        sys.stderr.write(
            "Error: Alpaca API credentials missing. Set APCA_API_KEY_ID / APCA_API_SECRET_KEY "
            f"or configure {CONFIG_PATH}\n"
        )
        sys.exit(1)

    return config


class AlpacaClient:
    def __init__(self, config: Dict[str, str]):
        self.key_id = config["key_id"]
        self.secret_key = config["secret_key"]
        self.base_url = config.get("base_url", "https://paper-api.alpaca.markets").rstrip("/")
        self.data_url = config.get("data_url", "https://data.alpaca.markets").rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.key_id,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HADES-Alpaca/1.0",
        }

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        is_data_api: bool = False,
    ) -> Any:
        base = self.data_url if is_data_api else self.base_url
        url = f"{base}{path}"
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            if query:
                url = f"{url}?{query}"

        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()
                if not content:
                    return {}
                return json.loads(content.decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="replace")
            sys.stderr.write(f"Alpaca API error [{e.code}]: {err_msg}\n")
            sys.exit(1)
        except urllib.error.URLError as e:
            sys.stderr.write(f"Connection failed: {e.reason}\n")
            sys.exit(1)


def cmd_status(client: AlpacaClient, args: argparse.Namespace) -> None:
    acct = client.request("GET", "/v2/account")
    clock = client.request("GET", "/v2/clock")

    if args.json:
        print(json.dumps({"account": acct, "clock": clock}, indent=2))
        return

    print("═════════════════════════════════════════════════════════════")
    print(f" ALPACA PAPER ACCOUNT: {acct.get('account_number')} [{acct.get('status', '').upper()}]")
    print("─────────────────────────────────────────────────────────────")
    print(f" Portfolio Value:   ${float(acct.get('portfolio_value', 0)):,.2f}")
    print(f" Cash:              ${float(acct.get('cash', 0)):,.2f}")
    print(f" Buying Power:      ${float(acct.get('buying_power', 0)):,.2f}")
    print(f" Daytrade Count:    {acct.get('daytrade_count', 0)}")
    print(f" Currency:          {acct.get('currency', 'USD')}")
    print(f" Market Open:       {'YES (Open)' if clock.get('is_open') else 'NO (Closed)'}")
    print(f" Next Market Open:  {clock.get('next_open')}")
    print(f" Next Market Close: {clock.get('next_close')}")
    print("═════════════════════════════════════════════════════════════")


def cmd_clock(client: AlpacaClient, args: argparse.Namespace) -> None:
    clock = client.request("GET", "/v2/clock")
    if args.json:
        print(json.dumps(clock, indent=2))
        return

    status_str = "OPEN" if clock.get("is_open") else "CLOSED"
    print(f"Market Status:     {status_str}")
    print(f"Current Timestamp: {clock.get('timestamp')}")
    print(f"Next Open:         {clock.get('next_open')}")
    print(f"Next Close:        {clock.get('next_close')}")


def cmd_positions(client: AlpacaClient, args: argparse.Namespace) -> None:
    positions = client.request("GET", "/v2/positions")
    if args.json:
        print(json.dumps(positions, indent=2))
        return

    if not positions:
        print("No open positions in portfolio.")
        return

    print(f"{'SYMBOL':<8} {'QTY':<8} {'AVG PRICE':<12} {'CURRENT':<12} {'MARKET VALUE':<14} {'UNREALIZED P&L':<16} {'CHG %':<8}")
    print("─" * 80)
    for p in positions:
        sym = p.get("symbol", "")
        qty = float(p.get("qty", 0))
        avg = float(p.get("avg_entry_price", 0))
        cur = float(p.get("current_price", 0))
        mv = float(p.get("market_value", 0))
        pl = float(p.get("unrealized_pl", 0))
        plpc = float(p.get("unrealized_plpc", 0)) * 100
        sign = "+" if pl >= 0 else ""
        print(f"{sym:<8} {qty:<8.2f} ${avg:<11.2f} ${cur:<11.2f} ${mv:<13.2f} {sign}${pl:<15.2f} {sign}{plpc:.2f}%")


def cmd_orders(client: AlpacaClient, args: argparse.Namespace) -> None:
    params = {"status": args.status, "limit": args.limit}
    orders = client.request("GET", "/v2/orders", params=params)
    if args.json:
        print(json.dumps(orders, indent=2))
        return

    if not orders:
        print(f"No {args.status} orders found.")
        return

    print(f"{'ID':<38} {'SYMBOL':<8} {'SIDE':<6} {'QTY':<8} {'TYPE':<8} {'STATUS':<10} {'SUBMITTED':<20}")
    print("─" * 102)
    for o in orders:
        oid = o.get("id", "")
        sym = o.get("symbol", "")
        side = o.get("side", "").upper()
        qty = o.get("qty") or f"${float(o.get('notional', 0)):.2f}"
        otype = o.get("type", "")
        status = o.get("status", "")
        sub = o.get("submitted_at", "")[:19]
        print(f"{oid:<38} {sym:<8} {side:<6} {qty:<8} {otype:<8} {status:<10} {sub:<20}")


def cmd_buy(client: AlpacaClient, args: argparse.Namespace) -> None:
    order_data: Dict[str, Any] = {
        "symbol": args.symbol.upper(),
        "side": "buy",
        "type": args.type,
        "time_in_force": args.tif,
    }

    if args.qty:
        order_data["qty"] = str(args.qty)
    elif args.notional:
        order_data["notional"] = str(args.notional)
    else:
        sys.stderr.write("Error: Must specify either --qty or --notional\n")
        sys.exit(1)

    if args.type == "limit":
        if not args.limit_price:
            sys.stderr.write("Error: --limit-price required for limit orders\n")
            sys.exit(1)
        order_data["limit_price"] = str(args.limit_price)

    if args.take_profit or args.stop_loss:
        order_data["order_class"] = "bracket"
        if args.take_profit:
            order_data["take_profit"] = {"limit_price": str(args.take_profit)}
        if args.stop_loss:
            order_data["stop_loss"] = {"stop_price": str(args.stop_loss)}

    res = client.request("POST", "/v2/orders", data=order_data)
    if args.json:
        print(json.dumps(res, indent=2))
        return

    print(f"BUY order placed: {res.get('id')} | {res.get('symbol')} {res.get('side')} {res.get('qty') or res.get('notional')} | Status: {res.get('status')}")


def cmd_sell(client: AlpacaClient, args: argparse.Namespace) -> None:
    if args.all:
        res = client.request("DELETE", f"/v2/positions/{args.symbol.upper()}")
        if args.json:
            print(json.dumps(res, indent=2))
            return
        print(f"Liquidated position in {args.symbol.upper()}.")
        return

    order_data: Dict[str, Any] = {
        "symbol": args.symbol.upper(),
        "side": "sell",
        "type": args.type,
        "time_in_force": args.tif,
    }

    if args.qty:
        order_data["qty"] = str(args.qty)
    else:
        sys.stderr.write("Error: Must specify either --qty or --all\n")
        sys.exit(1)

    if args.type == "limit":
        if not args.limit_price:
            sys.stderr.write("Error: --limit-price required for limit orders\n")
            sys.exit(1)
        order_data["limit_price"] = str(args.limit_price)

    res = client.request("POST", "/v2/orders", data=order_data)
    if args.json:
        print(json.dumps(res, indent=2))
        return

    print(f"SELL order placed: {res.get('id')} | {res.get('symbol')} {res.get('side')} {res.get('qty')} | Status: {res.get('status')}")


def cmd_cancel(client: AlpacaClient, args: argparse.Namespace) -> None:
    if args.all:
        res = client.request("DELETE", "/v2/orders")
        if args.json:
            print(json.dumps(res, indent=2))
            return
        print("Cancelled all open orders.")
        return

    if not args.order_id:
        sys.stderr.write("Error: Must specify order_id or --all\n")
        sys.exit(1)

    res = client.request("DELETE", f"/v2/orders/{args.order_id}")
    if args.json:
        print(json.dumps(res, indent=2))
        return
    print(f"Order {args.order_id} cancelled.")


def cmd_news(client: AlpacaClient, args: argparse.Namespace) -> None:
    params: Dict[str, Any] = {"limit": args.limit}
    if args.symbol:
        params["symbols"] = args.symbol.upper()

    res = client.request("GET", "/v1beta1/news", params=params, is_data_api=True)
    news_items = res.get("news", [])

    if args.json:
        print(json.dumps(news_items, indent=2))
        return

    if not news_items:
        print("No recent news items found.")
        return

    print(f"Found {len(news_items)} news items:")
    print("═" * 80)
    for item in news_items:
        headline = item.get("headline", "")
        symbols = ", ".join(item.get("symbols", []))
        author = item.get("author", "")
        created = item.get("created_at", "")[:19]
        url = item.get("url", "")
        summary = item.get("summary", "").strip().replace("\n", " ")

        print(f"[{created}] ({symbols or 'MACRO'}) - {headline}")
        if author:
            print(f" Source: {author}")
        if summary:
            print(f" Summary: {summary[:200]}...")
        if url:
            print(f" Link: {url}")
        print("─" * 80)


def cmd_bars(client: AlpacaClient, args: argparse.Namespace) -> None:
    symbol = args.symbol.upper()
    end_date = args.end or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = args.start or (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    params: Dict[str, Any] = {
        "symbols": symbol,
        "timeframe": args.timeframe,
        "limit": args.limit,
        "feed": "iex",
        "start": start_date,
        "end": end_date,
    }

    res = client.request("GET", "/v2/stocks/bars", params=params, is_data_api=True)
    bars = res.get("bars", {}).get(symbol, [])

    if args.json:
        print(json.dumps(bars, indent=2))
        return

    if not bars:
        print(f"No bars returned for {symbol} ({start_date} to {end_date}).")
        return

    print(f"Bars for {symbol} [{len(bars)} records]:")
    print(f"{'TIMESTAMP':<20} {'OPEN':<10} {'HIGH':<10} {'LOW':<10} {'CLOSE':<10} {'VOLUME':<12}")
    print("─" * 74)
    for b in bars:
        ts = b.get("t", "")[:19]
        o = float(b.get("o", 0))
        h = float(b.get("h", 0))
        l = float(b.get("l", 0))
        c = float(b.get("c", 0))
        v = int(b.get("v", 0))
        print(f"{ts:<20} ${o:<9.2f} ${h:<9.2f} ${l:<9.2f} ${c:<9.2f} {v:<12,d}")


def main() -> None:
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    parser = argparse.ArgumentParser(description="Alpaca Markets Tier-1 CLI", parents=[base_parser])
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_status = subparsers.add_parser("status", parents=[base_parser], aliases=["account"], help="Get account details, buying power & status")
    p_status.set_defaults(func=cmd_status)

    p_clock = subparsers.add_parser("clock", parents=[base_parser], help="Check market open/closed status")
    p_clock.set_defaults(func=cmd_clock)

    p_pos = subparsers.add_parser("positions", parents=[base_parser], help="List current portfolio positions")
    p_pos.set_defaults(func=cmd_positions)

    p_ord = subparsers.add_parser("orders", parents=[base_parser], help="List orders")
    p_ord.add_argument("--status", default="open", choices=["open", "closed", "all"], help="Filter order status")
    p_ord.add_argument("--limit", type=int, default=50, help="Max orders to return")
    p_ord.set_defaults(func=cmd_orders)

    p_buy = subparsers.add_parser("buy", parents=[base_parser], help="Place a buy order")
    p_buy.add_argument("symbol", help="Stock ticker symbol")
    p_buy.add_argument("--qty", type=float, help="Number of shares")
    p_buy.add_argument("--notional", type=float, help="Dollar amount to purchase")
    p_buy.add_argument("--type", default="market", choices=["market", "limit"], help="Order type")
    p_buy.add_argument("--limit-price", type=float, help="Limit price")
    p_buy.add_argument("--tif", default="day", choices=["day", "gtc", "ioc"], help="Time in force")
    p_buy.add_argument("--take-profit", type=float, help="Bracket take profit limit price")
    p_buy.add_argument("--stop-loss", type=float, help="Bracket stop loss price")
    p_buy.set_defaults(func=cmd_buy)

    p_sell = subparsers.add_parser("sell", parents=[base_parser], help="Place a sell order")
    p_sell.add_argument("symbol", help="Stock ticker symbol")
    p_sell.add_argument("--qty", type=float, help="Number of shares")
    p_sell.add_argument("--all", action="store_true", help="Liquidate entire position")
    p_sell.add_argument("--type", default="market", choices=["market", "limit"], help="Order type")
    p_sell.add_argument("--limit-price", type=float, help="Limit price")
    p_sell.add_argument("--tif", default="day", choices=["day", "gtc"], help="Time in force")
    p_sell.set_defaults(func=cmd_sell)

    p_cancel = subparsers.add_parser("cancel", parents=[base_parser], help="Cancel open order(s)")
    p_cancel.add_argument("order_id", nargs="?", help="Specific order ID to cancel")
    p_cancel.add_argument("--all", action="store_true", help="Cancel all open orders")
    p_cancel.set_defaults(func=cmd_cancel)

    p_news = subparsers.add_parser("news", parents=[base_parser], help="Fetch market news")
    p_news.add_argument("--symbol", help="Filter by ticker symbol")
    p_news.add_argument("--limit", type=int, default=10, help="Number of news articles")
    p_news.set_defaults(func=cmd_news)

    p_bars = subparsers.add_parser("bars", parents=[base_parser], help="Fetch historical OHLCV bars")
    p_bars.add_argument("symbol", help="Stock ticker symbol")
    p_bars.add_argument("--timeframe", default="1Day", choices=["1Min", "5Min", "15Min", "1Hour", "1Day"], help="Timeframe")
    p_bars.add_argument("--limit", type=int, default=10, help="Number of bars")
    p_bars.add_argument("--start", help="Start date (YYYY-MM-DD)")
    p_bars.add_argument("--end", help="End date (YYYY-MM-DD)")
    p_bars.set_defaults(func=cmd_bars)

    args = parser.parse_args()
    config = load_config()
    client = AlpacaClient(config)
    args.func(client, args)


if __name__ == "__main__":
    main()
