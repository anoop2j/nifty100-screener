import pandas as pd
import yfinance as yf
import json
import time
from datetime import datetime


OUTPUT_FILE = "data.json"


def get_nifty100_stocks():

    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"

    print("Downloading Nifty 100 stock list...")

    try:

        df = pd.read_csv(url)

        print(f"Total stocks found: {len(df)}")

        return df

    except Exception as e:

        print("Error downloading Nifty 100 list:", e)

        return None


def get_stock_data(symbol, company_name):

    try:

        yahoo_symbol = symbol.strip() + ".NS"

        print(f"Processing: {symbol}")

        df = yf.download(
            yahoo_symbol,
            period="2mo",
            progress=False,
            auto_adjust=False
        )

        if df.empty:

            return None

        # Last 20 trading sessions
        df = df.tail(20)

        # Handle yfinance multi-index columns
        high_column = df["High"]

        if isinstance(high_column, pd.DataFrame):
            high_column = high_column.iloc[:, 0]

        close_column = df["Close"]

        if isinstance(close_column, pd.DataFrame):
            close_column = close_column.iloc[:, 0]

        high_20 = float(high_column.max())

        latest_close = float(close_column.iloc[-1])

        latest_high = float(high_column.iloc[-1])

        high_date = high_column.idxmax()

        percent_from_high = (
            (latest_close - high_20)
            / high_20
        ) * 100

        return {

            "symbol": symbol,

            "company": company_name,

            "latest_close": round(latest_close, 2),

            "latest_high": round(latest_high, 2),

            "high_20_day": round(high_20, 2),

            "high_date": high_date.strftime("%d-%b-%Y"),

            "percent_from_high": round(
                percent_from_high,
                2
            )

        }

    except Exception as e:

        print(f"Error processing {symbol}: {e}")

        return None


def main():

    print("=" * 60)

    print("NIFTY 100 SCREENER STARTED")

    print("=" * 60)

    nifty_df = get_nifty100_stocks()

    results = []

    if nifty_df is not None:

        for index, row in nifty_df.iterrows():

            symbol = str(row["Symbol"]).strip()

            company_name = str(
                row.get("Company Name", "")
            ).strip()

            data = get_stock_data(
                symbol,
                company_name
            )

            if data:

                results.append(data)

            time.sleep(0.2)

    # Sort stocks closest to 20-day high

    results = sorted(
        results,
        key=lambda x: x["percent_from_high"],
        reverse=True
    )

    output = {

        "last_updated": datetime.now().strftime(
            "%d-%b-%Y %I:%M %p"
        ),

        "total_stocks": len(results),

        "stocks": results

    }

    # Always create JSON file

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

    print("DATA FILE CREATED")

    print(f"Total Stocks: {len(results)}")

    print(f"File: {OUTPUT_FILE}")

    print("=" * 60)


if __name__ == "__main__":

    main()
