import pandas as pd
import yfinance as yf
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================================================

# CONFIGURATION

# =========================================================

SYMBOL_FILE = "nifty100_symbols.csv"
OUTPUT_FILE = "data.json"

TARGET_PERCENT = 6
LOOKBACK_DAYS = 20

# Approximately one year of trading days

ANALYSIS_TRADING_DAYS = 252

# =========================================================

# DOWNLOAD STOCK DATA

# =========================================================

def download_stock_data(symbol):

```
try:

    yahoo_symbol = symbol + ".NS"

    print(f"Downloading data for: {symbol}")

    df = yf.download(
        yahoo_symbol,
        period="18mo",
        interval="1d",
        progress=False,
        auto_adjust=False
    )

    if df.empty:

        print(f"  No data found for {symbol}")

        return None


    # Handle yfinance MultiIndex columns

    if isinstance(df.columns, pd.MultiIndex):

        df.columns = df.columns.get_level_values(0)


    # Remove rows with missing values

    df = df.dropna(
        subset=[
            "High",
            "Low",
            "Close"
        ]
    )


    return df


except Exception as e:

    print(
        f"  ERROR downloading {symbol}: {e}"
    )

    return None
```

# =========================================================

# CALCULATE CURRENT VALUES

# =========================================================

def calculate_current_values(df):

```
"""
Calculate:

1. Latest available closing price
2. Highest High of latest 20 trading days
3. Distance of latest close from 20-day high
"""


recent_df = df.tail(
    LOOKBACK_DAYS
)


high_20_day = (
    recent_df["High"].max()
)


# Latest available trading-day close

yesterday_close = (
    df["Close"].iloc[-1]
)


away_percent = (

    (
        yesterday_close
        -
        high_20_day
    )

    /

    high_20_day

) * 100


return {

    "yesterday_close":
        round(
            float(yesterday_close),
            2
        ),

    "high_20_day":
        round(
            float(high_20_day),
            2
        ),

    "away_percent":
        round(
            float(away_percent),
            2
        )

}
```

# =========================================================

# CHECK NEW 20-DAY LOW

# =========================================================

def is_new_20_day_low(
df,
index
):

```
"""
Returns True when the current day's
Low is lower than the lowest Low of
the previous 20 trading days.
"""


if index < LOOKBACK_DAYS:

    return False


previous_20_low = (

    df["Low"]
    .iloc[
        index - LOOKBACK_DAYS:index
    ]
    .min()

)


current_low = (

    df["Low"]
    .iloc[index]

)


return (
    current_low < previous_20_low
)
```

# =========================================================

# ANALYSE BREAKOUT STRATEGY

# =========================================================

def analyse_breakouts(df):

```
"""
STRATEGY LOGIC

1. Analyse approximately the last 1 year.

2. Detect a fresh 20-day high breakout.

3. Breakout level =
   Highest High of previous 20 trading days.

4. Target =
   Breakout level + 6%.

5. After breakout:

   If 6% target is achieved FIRST:
       Target Met YES

   If new 20-day LOW is created FIRST:
       Target Met NO

6. If neither event occurs before the
   end of the analysis period:
       Pending

7. Pending signals are NOT included
   in Strike Rate.

8. Strike Rate =
   Target Yes /
   (Target Yes + Target No) × 100
"""


target_yes = 0

target_no = 0

pending = 0


# -----------------------------------------------------
# Keep additional 20 days of history so that the
# first day of the one-year analysis has enough data
# for calculating the previous 20-day high/low.
# -----------------------------------------------------

required_days = (

    ANALYSIS_TRADING_DAYS
    +
    LOOKBACK_DAYS

)


analysis_df = df.tail(
    required_days
).copy()


if len(analysis_df) <= LOOKBACK_DAYS:

    return {

        "target_yes": 0,

        "target_no": 0,

        "pending": 0,

        "strike_rate": 0

    }


# -----------------------------------------------------
# Prevent consecutive new highs from being counted
# as separate breakout signals.
#
# A new signal becomes possible only after the stock
# moves back below its previous 20-day high.
# -----------------------------------------------------

breakout_active = False


# -----------------------------------------------------
# SCAN THE ONE-YEAR PERIOD
# -----------------------------------------------------

for i in range(
    LOOKBACK_DAYS,
    len(analysis_df)
):


    # -------------------------------------------------
    # Previous 20-day High
    # -------------------------------------------------

    previous_20_high = (

        analysis_df["High"]
        .iloc[
            i - LOOKBACK_DAYS:i
        ]
        .max()

    )


    current_high = (

        analysis_df["High"]
        .iloc[i]

    )


    # -------------------------------------------------
    # If today's High does not exceed the previous
    # 20-day High, reset breakout status.
    # -------------------------------------------------

    if current_high <= previous_20_high:

        breakout_active = False


    # -------------------------------------------------
    # FRESH 20-DAY HIGH BREAKOUT
    # -------------------------------------------------

    if (

        current_high > previous_20_high

        and

        breakout_active is False

    ):


        breakout_active = True


        # ---------------------------------------------
        # BREAKOUT / ENTRY PRICE
        # ---------------------------------------------

        breakout_price = (
            previous_20_high
        )


        # ---------------------------------------------
        # 6% TARGET
        # ---------------------------------------------

        target_price = (

            breakout_price

            *

            (
                1
                +
                TARGET_PERCENT / 100
            )

        )


        breakout_result = None


        # ---------------------------------------------
        # CHECK EVERY FUTURE TRADING DAY
        # ---------------------------------------------

        for j in range(
            i + 1,
            len(analysis_df)
        ):


            future_high = (

                analysis_df["High"]
                .iloc[j]

            )


            # -----------------------------------------
            # EVENT 1:
            # 6% TARGET ACHIEVED
            # -----------------------------------------

            if future_high >= target_price:

                breakout_result = "YES"

                break


            # -----------------------------------------
            # EVENT 2:
            # NEW 20-DAY LOW
            # -----------------------------------------

            if is_new_20_day_low(
                analysis_df,
                j
            ):

                breakout_result = "NO"

                break


        # ---------------------------------------------
        # RECORD RESULT
        # ---------------------------------------------

        if breakout_result == "YES":

            target_yes += 1


        elif breakout_result == "NO":

            target_no += 1


        else:

            # Neither target nor new 20-day low
            # occurred before end of analysis.

            pending += 1


# =====================================================
# CALCULATE STRIKE RATE
# =====================================================

completed_signals = (

    target_yes
    +
    target_no

)


if completed_signals > 0:

    strike_rate = (

        target_yes
        /
        completed_signals

    ) * 100

else:

    strike_rate = 0


# =====================================================
# RETURN BREAKOUT RESULTS
# =====================================================

return {

    "target_yes":
        target_yes,

    "target_no":
        target_no,

    "pending":
        pending,

    "strike_rate":
        round(
            strike_rate,
            2
        )

}
```

# =========================================================

# PROCESS SINGLE STOCK

# =========================================================

def process_stock(
symbol,
company
):

```
try:


    # -------------------------------------------------
    # DOWNLOAD DATA
    # -------------------------------------------------

    df = download_stock_data(
        symbol
    )


    if df is None:

        return None


    # -------------------------------------------------
    # CHECK DATA AVAILABILITY
    # -------------------------------------------------

    minimum_required = (

        ANALYSIS_TRADING_DAYS
        +
        LOOKBACK_DAYS

    )


    if len(df) < minimum_required:

        print(
            f"  Insufficient data for {symbol}"
        )

        return None


    # -------------------------------------------------
    # CURRENT 20-DAY VALUES
    # -------------------------------------------------

    current_data = (

        calculate_current_values(
            df
        )

    )


    # -------------------------------------------------
    # BREAKOUT ANALYSIS
    # -------------------------------------------------

    breakout_data = (

        analyse_breakouts(
            df
        )

    )


    # -------------------------------------------------
    # CREATE RESULT
    # -------------------------------------------------

    result = {

        "symbol":
            symbol,

        "company":
            company,

        "yesterday_close":
            current_data[
                "yesterday_close"
            ],

        "high_20_day":
            current_data[
                "high_20_day"
            ],

        "away_percent":
            current_data[
                "away_percent"
            ],

        "target_yes":
            breakout_data[
                "target_yes"
            ],

        "target_no":
            breakout_data[
                "target_no"
            ],

        "pending":
            breakout_data[
                "pending"
            ],

        "strike_rate":
            breakout_data[
                "strike_rate"
            ]

    }


    return result


except Exception as e:

    print(
        f"ERROR processing {symbol}: {e}"
    )

    return None
```

# =========================================================

# MAIN PROGRAM

# =========================================================

def main():

```
print()

print("=" * 70)

print(
    "NIFTY 100 BREAKOUT & STRIKE RATE SCREENER"
)

print("=" * 70)

print()


# -----------------------------------------------------
# READ STOCK LIST
# -----------------------------------------------------

try:

    stocks = pd.read_csv(
        SYMBOL_FILE
    )

except Exception as e:

    print()

    print(
        f"ERROR reading {SYMBOL_FILE}: {e}"
    )

    return


print(
    f"Total stocks to process: {len(stocks)}"
)

print()


print("-" * 70)


results = []


# -----------------------------------------------------
# PROCESS ALL STOCKS
# -----------------------------------------------------

for index, row in stocks.iterrows():


    symbol = str(
        row["symbol"]
    ).strip()


    company = str(
        row["company"]
    ).strip()


    print()

    print(

        f"[{index + 1}/{len(stocks)}] "
        f"Processing {symbol}"

    )


    result = process_stock(

        symbol,

        company

    )


    if result is not None:


        results.append(
            result
        )


        print(

            f"  Close       : "
            f"₹{result['yesterday_close']}"

        )


        print(

            f"  20D High    : "
            f"₹{result['high_20_day']}"

        )


        print(

            f"  Away        : "
            f"{result['away_percent']}%"

        )


        print(

            f"  Target Yes  : "
            f"{result['target_yes']}"

        )


        print(

            f"  Target No   : "
            f"{result['target_no']}"

        )


        print(

            f"  Pending     : "
            f"{result['pending']}"

        )


        print(

            f"  Strike Rate : "
            f"{result['strike_rate']}%"

        )


    # -------------------------------------------------
    # Small delay between requests
    # -------------------------------------------------

    time.sleep(0.3)


# =====================================================
# SORT RESULTS
# =====================================================

results.sort(

    key=lambda x: (

        x["strike_rate"],

        x["away_percent"]

    ),

    reverse=True

)


# =====================================================
# IST TIMESTAMP
# =====================================================

ist_now = datetime.now(
    ZoneInfo("Asia/Kolkata")
)


last_updated = ist_now.strftime(
    "%d-%b-%Y %I:%M %p IST"
)


# =====================================================
# CREATE JSON OUTPUT
# =====================================================

output = {

    "last_updated":
        last_updated,

    "total_stocks":
        len(results),

    "strategy": {

        "breakout":
            "Fresh 20-day high breakout",

        "target":
            "6% above breakout level",

        "success_condition":
            "6% target achieved before a new 20-day low",

        "failure_condition":
            "New 20-day low before 6% target",

        "analysis_period":
            "Last 1 year",

        "pending_condition":
            "Neither target nor new 20-day low achieved",

        "strike_rate_formula":
            "Target Yes / (Target Yes + Target No) * 100"

    },

    "stocks":
        results

}


# =====================================================
# WRITE DATA.JSON
# =====================================================

try:

    with open(

        OUTPUT_FILE,

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            output,

            f,

            indent=4,

            ensure_ascii=False

        )


except Exception as e:

    print()

    print(
        f"ERROR writing {OUTPUT_FILE}: {e}"
    )

    return


# =====================================================
# FINAL SUMMARY
# =====================================================

print()

print("=" * 70)

print(
    "PROCESS COMPLETED"
)

print("=" * 70)

print()

print(
    f"Successful stocks : {len(results)}"
)

print(
    f"Total stocks      : {len(stocks)}"
)

print(
    f"Last Updated      : {last_updated}"
)

print(
    f"Output File       : {OUTPUT_FILE}"
)

print()

print("=" * 70)
```

# =========================================================

# PROGRAM ENTRY POINT

# =========================================================

if **name** == "**main**":

```
main()
```
