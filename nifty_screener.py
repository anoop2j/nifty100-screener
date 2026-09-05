import pandas as pd
import yfinance as yf
import json
import time
from datetime import datetime


SYMBOL_FILE = "nifty100_symbols.csv"
OUTPUT_FILE = "data.json"


def get_stock_data(symbol, company):

    try:

        yahoo_symbol = symbol.replace("&", "%26") + ".NS"

        print(f"Processing {symbol}...")

        df = yf.download(
            yahoo_symbol,
            period="2mo",
            interval="1d",
            progress=False,
            auto_adjust=False
        )

        if df.empty:

            print(f"  No data: {symbol}")

            return None

        # Handle yfinance MultiIndex
        if isinstance(df.columns, pd.MultiIndex):

            high = df["High"].iloc[:, 0]

            close = df["Close"].iloc[:, 0]

        else:

            high = df["High"]

            close = df["Close"]

        # Last 20 trading days
        high = high.tail(20)

        close = close.tail(20)

        if len(high) == 0:

            return None

        high_20 = float(high.max())

        latest_close = float(close.iloc[-1])

        latest_high = float(high.iloc[-1])

        high_date = high.idxmax()

        percent_from_high = (
            (latest_close - high_20)
            / high_20
        ) * 100

        return {

            "symbol": symbol,

            "company": company,

            "latest_close": round(
                latest_close,
                2
            ),

            "latest_high": round(
                latest_high,
                2
            ),

            "high_20_day": round(
                high_20,
                2
            ),

            "high_date":
                high_date.strftime(
                    "%d-%b-%Y"
                ),

            "percent_from_high":
                round(
                    percent_from_high,
                    2
                )

        }

    except Exception as e:

        print(
            f"  ERROR {symbol}: {e}"
        )

        return None


def main():

    print("=" * 60)

    print("NIFTY 100 SCREENER")

    print("=" * 60)


    # Read our local stock list

    try:

        stocks = pd.read_csv(
            SYMBOL_FILE
        )

    except Exception as e:

        print(
            "ERROR reading symbol file:",
            e
        )

        raise


    print(
        f"Stocks to process: {len(stocks)}"
    )


    results = []


    for index, row in stocks.iterrows():

        symbol = str(
            row["symbol"]
        ).strip()

        company = str(
            row["company"]
        ).strip()


        print(
            f"[{index + 1}/{len(stocks)}] "
            f"{symbol}"
        )


        result = get_stock_data(
            symbol,
            company
        )


        if result:

            results.append(result)


        time.sleep(0.5)


    # Sort by distance from 20-day high

    results.sort(
        key=lambda x:
            x["percent_from_high"],
        reverse=True
    )


    output = {

        "last_updated":
            datetime.now().strftime(
                "%d-%b-%Y %I:%M %p"
            ),

        "total_stocks":
            len(results),

        "stocks":
            results

    }


    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4
        )


    print("=" * 60)

    print(
        f"Successful stocks: "
        f"{len(results)}"
    )

    print(
        f"Data written to: "
        f"{OUTPUT_FILE}"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()
