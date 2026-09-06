import pandas as pd
import yfinance as yf
import json
import time
from datetime import datetime


SYMBOL_FILE = "nifty100_symbols.csv"
OUTPUT_FILE = "data.json"


# ---------------------------------------------------------
# GET HISTORICAL STOCK DATA
# ---------------------------------------------------------

def download_stock_data(symbol):

    try:

        yahoo_symbol = symbol + ".NS"

        print(f"Downloading: {symbol}")

        df = yf.download(
            yahoo_symbol,
            period="18mo",
            interval="1d",
            progress=False,
            auto_adjust=False
        )

        if df.empty:

            print(f"No data found for {symbol}")

            return None

        # Handle yfinance multi-index columns

        if isinstance(df.columns, pd.MultiIndex):

            df.columns = df.columns.get_level_values(0)

        return df

    except Exception as e:

        print(f"ERROR downloading {symbol}: {e}")

        return None


# ---------------------------------------------------------
# CALCULATE CURRENT 20 DAY HIGH
# ---------------------------------------------------------

def calculate_current_values(df):

    # Last 20 completed trading days

    recent_df = df.tail(20)

    high_20_day = recent_df["High"].max()

    # Yesterday close
    # Last available trading day's close

    yesterday_close = df["Close"].iloc[-1]

    away_percent = (
        (yesterday_close - high_20_day)
        / high_20_day
    ) * 100

    return {

        "yesterday_close":
            round(float(yesterday_close), 2),

        "high_20_day":
            round(float(high_20_day), 2),

        "away_percent":
            round(float(away_percent), 2)

    }


# ---------------------------------------------------------
# ANALYSE BREAKOUT HISTORY
# ---------------------------------------------------------

def analyse_breakouts(df):

    # Use approximately last 1 year
    # 252 trading days

    analysis_df = df.tail(272).copy()

    target_yes = 0

    target_no = 0

    breakout_active = False


    # Start from day 20

    for i in range(20, len(analysis_df)):

        # Previous 20-day high

        previous_20_high = (
            analysis_df["High"]
            .iloc[i - 20:i]
            .max()
        )

        today_high = (
            analysis_df["High"]
            .iloc[i]
        )


        # -------------------------------------------------
        # RESET BREAKOUT STATE
        # -------------------------------------------------

        # If stock goes below previous 20-day high,
        # allow next fresh breakout

        if today_high < previous_20_high:

            breakout_active = False


        # -------------------------------------------------
        # DETECT FRESH BREAKOUT
        # -------------------------------------------------

        if (
            today_high > previous_20_high
            and breakout_active is False
        ):

            breakout_active = True

            breakout_price = previous_20_high

            target_price = breakout_price * 1.06


            # ---------------------------------------------
            # CHECK ALL FUTURE DAYS UNTIL TODAY
            # ---------------------------------------------

            future_data = analysis_df.iloc[i + 1:]


            if future_data.empty:

                # Latest breakout cannot be evaluated yet

                target_no += 1

                continue


            future_high = (
                future_data["High"].max()
            )


            if future_high >= target_price:

                target_yes += 1

            else:

                target_no += 1


    total_signals = (
        target_yes + target_no
    )


    if total_signals > 0:

        strike_rate = (
            target_yes / total_signals
        ) * 100

    else:

        strike_rate = 0


    return {

        "target_yes": target_yes,

        "target_no": target_no,

        "strike_rate":
            round(strike_rate, 2)

    }


# ---------------------------------------------------------
# PROCESS ONE STOCK
# ---------------------------------------------------------

def process_stock(symbol, company):

    try:

        df = download_stock_data(symbol)

        if df is None or len(df) < 50:

            return None


        # Current values

        current_data = (
            calculate_current_values(df)
        )


        # Historical breakout analysis

        breakout_data = (
            analyse_breakouts(df)
        )


        return {

            "symbol": symbol,

            "company": company,

            "yesterday_close":
                current_data["yesterday_close"],

            "high_20_day":
                current_data["high_20_day"],

            "away_percent":
                current_data["away_percent"],

            "target_yes":
                breakout_data["target_yes"],

            "target_no":
                breakout_data["target_no"],

            "strike_rate":
                breakout_data["strike_rate"]

        }


    except Exception as e:

        print(f"ERROR processing {symbol}: {e}")

        return None


# ---------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------

def main():

    print("=" * 60)

    print("NIFTY 100 BREAKOUT SCREENER")

    print("=" * 60)


    # Read stock symbols

    stocks = pd.read_csv(
        SYMBOL_FILE
    )


    print(
        f"Total stocks to process: {len(stocks)}"
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
            f"Processing {symbol}"
        )


        result = process_stock(
            symbol,
            company
        )


        if result:

            results.append(result)


        # Avoid excessive Yahoo requests

        time.sleep(0.3)


    # -----------------------------------------------------
    # SORT BY STRIKE RATE
    # -----------------------------------------------------

    results.sort(

        key=lambda x: (
            x["strike_rate"],
            x["away_percent"]
        ),

        reverse=True

    )


    # -----------------------------------------------------
    # CREATE JSON OUTPUT
    # -----------------------------------------------------

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

    print("PROCESS COMPLETED")

    print(
        f"Successful stocks: {len(results)}"
    )

    print(
        f"File created: {OUTPUT_FILE}"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()
