import pandas as pd
import yfinance as yf
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# SETTINGS
# ============================================================

SYMBOL_FILE = "nifty100_symbols.csv"
OUTPUT_FILE = "data.json"

LOOKBACK_DAYS = 20
TARGET_PERCENT = 6
ANALYSIS_TRADING_DAYS = 252


# ============================================================
# DOWNLOAD STOCK DATA
# ============================================================

def download_stock_data(symbol):

    yahoo_symbol = symbol + ".NS"

    print("Downloading:", yahoo_symbol)

    try:

        df = yf.download(
            yahoo_symbol,
            period="18mo",
            interval="1d",
            progress=False,
            auto_adjust=False
        )

        if df.empty:
            return None

        # Handle yfinance MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        required_columns = ["High", "Low", "Close"]

        for column in required_columns:
            if column not in df.columns:
                return None

        df = df.dropna(
            subset=required_columns
        ).reset_index()

        # Convert numeric values
        for column in required_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        df = df.dropna(
            subset=required_columns
        ).reset_index(drop=True)

        if len(df) < LOOKBACK_DAYS + 1:
            return None

        df["Date"] = pd.to_datetime(
            df["Date"]
        ).dt.date

        return df

    except Exception as e:

        print(
            "Error downloading",
            symbol,
            ":",
            e
        )

        return None


# ============================================================
# CURRENT STOCK VALUES
# ============================================================

def calculate_current_values(df):

    latest_close = float(
        df["Close"].iloc[-1]
    )

    last_20_high = float(
        df["High"].tail(
            LOOKBACK_DAYS
        ).max()
    )

    if last_20_high > 0:

        away_percent = (
            (last_20_high - latest_close)
            / last_20_high
        ) * 100

    else:

        away_percent = 0

    return (
        latest_close,
        last_20_high,
        away_percent
    )


# ============================================================
# CHECK NEW 20-DAY LOW
# ============================================================

def is_new_20_day_low(data, index):

    if index < LOOKBACK_DAYS:
        return False

    previous_20_low = float(
        data["Low"].iloc[
            index - LOOKBACK_DAYS:index
        ].min()
    )

    current_low = float(
        data["Low"].iloc[index]
    )

    return current_low < previous_20_low


# ============================================================
# ANALYSE BREAKOUT TRANSACTIONS
# ============================================================

def analyse_breakouts(df):

    required_days = (
        ANALYSIS_TRADING_DAYS
        + LOOKBACK_DAYS
    )

    analysis_df = df.tail(
        required_days
    ).copy().reset_index(drop=True)

    transactions = []

    # Start after first 20 days
    i = LOOKBACK_DAYS

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # False = normal breakout scanning
    #
    # True = target was achieved and we MUST WAIT
    #        for a new 20-day low before another breakout.
    # --------------------------------------------------------

    wait_for_new_low_after_target = False


    while i < len(analysis_df):

        # ====================================================
        # AFTER TARGET ACHIEVED
        #
        # DO NOT SEARCH FOR BREAKOUT.
        #
        # WAIT FOR NEW 20-DAY LOW.
        # ====================================================

        if wait_for_new_low_after_target:

            if is_new_20_day_low(
                analysis_df,
                i
            ):

                print(
                    "New 20-day low found after target:",
                    analysis_df["Date"].iloc[i]
                )

                # Trading cycle can restart
                wait_for_new_low_after_target = False

            else:

                i += 1
                continue


        # ====================================================
        # CALCULATE PREVIOUS 20-DAY HIGH
        # ====================================================

        previous_20_high = float(
            analysis_df["High"].iloc[
                i - LOOKBACK_DAYS:i
            ].max()
        )

        current_high = float(
            analysis_df["High"].iloc[i]
        )


        # ====================================================
        # FRESH 20-DAY HIGH BREAKOUT
        # ====================================================

        if current_high > previous_20_high:

            breakout_date = (
                analysis_df["Date"].iloc[i]
            )

            # Entry = previous 20-day high
            breakout_price = previous_20_high

            # Target = +6%
            target_price = (
                breakout_price
                * (1 + TARGET_PERCENT / 100)
            )

            result = "PENDING"

            result_date = None

            days_to_result = None

            target_met_yes_date = None

            target_met_no_date = None


            # =================================================
            # CHECK DAYS AFTER BREAKOUT
            # =================================================

            j = i + 1

            while j < len(analysis_df):

                future_date = (
                    analysis_df["Date"].iloc[j]
                )

                future_high = float(
                    analysis_df["High"].iloc[j]
                )


                # =============================================
                # TARGET +6% ACHIEVED
                # =============================================

                if future_high >= target_price:

                    result = "TARGET MET YES"

                    result_date = future_date

                    target_met_yes_date = (
                        future_date
                    )

                    days_to_result = j - i

                    break


                # =============================================
                # NEW 20-DAY LOW BEFORE TARGET
                # =============================================

                if is_new_20_day_low(
                    analysis_df,
                    j
                ):

                    result = "TARGET MET NO"

                    result_date = future_date

                    target_met_no_date = (
                        future_date
                    )

                    days_to_result = j - i

                    break


                j += 1


            # =================================================
            # SAVE TRANSACTION
            # =================================================

            transactions.append({

                "Stock Code": symbol_name_from_df(
                    df
                ),

                "Breakout Date": breakout_date,

                "Breakout Price": round(
                    breakout_price,
                    2
                ),

                "Target Price": round(
                    target_price,
                    2
                ),

                "Target Met Yes Date":
                    target_met_yes_date,

                "Target Met No Date":
                    target_met_no_date,

                "Result":
                    result,

                "Result Date":
                    result_date,

                "Days to Result":
                    days_to_result
            })


            # =================================================
            # NEW TRADE-CYCLE LOGIC
            # =================================================

            if result == "TARGET MET YES":

                # Target achieved.
                #
                # DO NOT immediately search for another
                # breakout.
                #
                # Wait for a NEW 20-DAY LOW.

                wait_for_new_low_after_target = True

                i = j + 1


            elif result == "TARGET MET NO":

                # New 20-day low has already occurred.
                #
                # We can start looking for the next breakout
                # after this day.

                wait_for_new_low_after_target = False

                i = j + 1


            else:

                # Still pending
                i += 1


        else:

            i += 1


    return transactions


# ============================================================
# HELPER
# ============================================================

def symbol_name_from_code(symbol):

    return symbol


def symbol_name_from_df(df):

    return getattr(
        df,
        "_symbol_name",
        ""
    )


# ============================================================
# PROCESS ONE STOCK
# ============================================================

def process_stock(symbol):

    df = download_stock_data(
        symbol
    )

    if df is None:

        return None, []


    # Store symbol name inside dataframe
    df._symbol_name = symbol


    # ========================================================
    # CURRENT VALUES
    # ========================================================

    (
        latest_close,
        last_20_high,
        away_percent
    ) = calculate_current_values(
        df
    )


    # ========================================================
    # HISTORICAL TRANSACTIONS
    # ========================================================

    transactions = analyse_breakouts(
        df
    )


    # ========================================================
    # STATISTICS
    # ========================================================

    target_yes = len([
        x for x in transactions
        if x["Result"] == "TARGET MET YES"
    ])

    target_no = len([
        x for x in transactions
        if x["Result"] == "TARGET MET NO"
    ])

    pending = len([
        x for x in transactions
        if x["Result"] == "PENDING"
    ])


    completed = (
        target_yes
        + target_no
    )


    if completed > 0:

        strike_rate = (
            target_yes
            / completed
        ) * 100

    else:

        strike_rate = 0


    # ========================================================
    # SUMMARY
    # ========================================================

    summary = {

        "Stock Code":
            symbol,

        "Yesterday Close":
            round(
                latest_close,
                2
            ),

        "20 Day High":
            round(
                last_20_high,
                2
            ),

        "20 Day High Away %":
            round(
                away_percent,
                2
            ),

        "Target Met Yes":
            target_yes,

        "Target Met No":
            target_no,

        "Pending":
            pending,

        "Strike Rate":
            round(
                strike_rate,
                2
            )
    }


    return summary, transactions


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print()
    print("=" * 70)
    print("NIFTY 100 SCREENER")
    print("=" * 70)
    print()


    # ========================================================
    # READ SYMBOL FILE
    # ========================================================

    try:

        symbols_df = pd.read_csv(
            SYMBOL_FILE
        )

    except Exception as e:

        print(
            "Unable to read",
            SYMBOL_FILE,
            ":",
            e
        )

        return


    # Find stock-code column
    possible_columns = [
        "Stock Code",
        "Symbol",
        "SYMBOL",
        "symbol"
    ]

    symbol_column = None

    for column in possible_columns:

        if column in symbols_df.columns:

            symbol_column = column
            break


    if symbol_column is None:

        print(
            "ERROR: CSV must contain a Stock Code or Symbol column."
        )

        return


    symbols = (
        symbols_df[symbol_column]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )


    print(
        "Stocks found:",
        len(symbols)
    )

    print()


    # ========================================================
    # PROCESS STOCKS
    # ========================================================

    summary_results = []

    all_transactions = []


    for count, symbol in enumerate(
        symbols,
        start=1
    ):

        print(
            "[",
            count,
            "/",
            len(symbols),
            "] Processing",
            symbol
        )


        try:

            summary, transactions = (
                process_stock(symbol)
            )


            if summary is not None:

                summary_results.append(
                    summary
                )


                for transaction in transactions:

                    transaction[
                        "Stock Code"
                    ] = symbol

                    all_transactions.append(
                        transaction
                    )


        except Exception as e:

            print(
                "Error processing",
                symbol,
                ":",
                e
            )


        # Small delay to reduce Yahoo Finance rate-limit risk
        time.sleep(0.5)


    # ========================================================
    # SORT SUMMARY
    #
    # 20 Day High Away % - MOST NEAR FIRST
    #
    # Example:
    # 0.50%
    # 1.20%
    # 2.10%
    # 3.50%
    # ...
    # ========================================================

    summary_results = sorted(
        summary_results,
        key=lambda x: x[
            "20 Day High Away %"
        ]
    )


    # ========================================================
    # CREATE DATA.JSON
    # ========================================================

    ist_now = datetime.now(
        ZoneInfo("Asia/Kolkata")
    )


    output_data = {

        "updated": ist_now.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "stocks": summary_results
    }


    try:

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                output_data,
                f,
                indent=2
            )


        print()
        print(
            "data.json created successfully."
        )


    except Exception as e:

        print(
            "Error creating data.json:",
            e
        )


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("PROCESS COMPLETED")
    print("=" * 70)

    print(
        "Stocks processed:",
        len(summary_results)
    )

    print(
        "Total transactions:",
        len(all_transactions)
    )

    print(
        "Output file:",
        OUTPUT_FILE
    )

    print()

    print(
        "SORTING:",
        "20 Day High Away % - MOST NEAR FIRST"
    )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
