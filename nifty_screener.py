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

LOOKBACK_DAYS = 20
TARGET_PERCENT = 6

# Number of trading days approximately equal to one year

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

        print(f"No data found for {symbol}")

        return None

    # Handle MultiIndex columns returned by yfinance

    if isinstance(df.columns, pd.MultiIndex):

        df.columns = df.columns.get_level_values(0)

    # Remove incomplete rows

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
        f"Error downloading {symbol}: {e}"
    )

    return None
```

# =========================================================

# CURRENT MARKET VALUES

# =========================================================

def calculate_current_values(df):

```
recent_df = df.tail(
    LOOKBACK_DAYS
)

high_20_day = (
    recent_df["High"].max()
)

latest_close = (
    df["Close"].iloc[-1]
)

away_percent = (
    (
        latest_close - high_20_day
    )
    /
    high_20_day
) * 100

return {

    "yesterday_close":
        round(
            float(latest_close),
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

# CHECK IF CURRENT DAY CREATES A NEW 20-DAY LOW

# =========================================================

def is_new_20_day_low(df, index):

```
"""
A new 20-day low occurs when today's Low is lower than
every Low during the previous 20 trading days.
"""

if index < LOOKBACK_DAYS:

    return False

previous_20_day_low = (
    df["Low"]
    .iloc[
        index - LOOKBACK_DAYS:index
    ]
    .min()
)

current_low = (
    df["Low"].iloc[index]
)

return current_low < previous_20_day_low
```

# =========================================================

# ANALYSE 20-DAY BREAKOUTS FOR LAST ONE YEAR

# =========================================================

def analyse_breakouts(df):

```
"""
STRATEGY LOGIC

ANALYSIS PERIOD:
    Last 252 trading days.

BREAKOUT:
    Current day's High is greater than the highest High
    of the previous 20 trading days.

TARGET:
    Previous 20-day High + 6%.

TARGET MET YES:
    After breakout, stock reaches 6% target BEFORE
    creating a new 20-day low.

TARGET MET NO:
    After breakout, stock creates a new 20-day low
    BEFORE reaching the 6% target.

PENDING:
    Neither target nor new 20-day low occurs before
    the end of the one-year analysis period.

STRIKE RATE:
    Target Yes /
    (Target Yes + Target No)
    * 100
"""

target_yes = 0
target_no = 0
pending = 0

# We need 20 extra days before the analysis period
# for correct breakout calculations.

required_days = (
    ANALYSIS_TRADING_DAYS
    +
    LOOKBACK_DAYS
)

analysis_df = (
    df.tail(required_days)
    .copy()
    .reset_index(drop=True)
)

if len(analysis_df) <= LOOKBACK_DAYS:

    return {

        "target_yes": 0,
        "target_no": 0,
        "pending": 0,
        "strike_rate": 0
    }

# -----------------------------------------------------
# Scan for breakout signals
# -----------------------------------------------------

i = LOOKBACK_DAYS

while i < len(analysis_df):

    # Previous 20-day high

    previous_20_day_high = (
        analysis_df["High"]
        .iloc[
            i - LOOKBACK_DAYS:i
        ]
        .max()
    )

    current_high = (
        analysis_df["High"].iloc[i]
    )

    # -------------------------------------------------
    # CHECK FOR FRESH 20-DAY HIGH BREAKOUT
    # -------------------------------------------------

    if current_high > previous_20_day_high:

        breakout_level = (
            previous_20_day_high
        )

        target_price = (
            breakout_level
            *
            (1 + TARGET_PERCENT / 100)
        )

        breakout_result = None

        # Start monitoring from the breakout day itself
        # and subsequent days.

        j = i

        while j < len(analysis_df):

            day_high = (
                analysis_df["High"].iloc[j]
            )

            # -----------------------------------------
            # CONDITION 1
            # TARGET OF 6% ACHIEVED
            # -----------------------------------------

            if day_high >= target_price:

                breakout_result = "YES"

                break

            # -----------------------------------------
            # CONDITION 2
            # NEW 20-DAY LOW CREATED
            # -----------------------------------------

            if (
                j > i
                and
                is_new_20_day_low(
                    analysis_df,
                    j
                )
            ):

                breakout_result = "NO"

                break

            j += 1

        # ---------------------------------------------
        # UPDATE COUNTERS
        # ---------------------------------------------

        if breakout_result == "YES":

            target_yes += 1

        elif breakout_result == "NO":

            target_no += 1

        else:

            pending += 1

        # ---------------------------------------------
        # IMPORTANT:
        #
        # Move scanner after this trade is completed.
        #
        # This prevents multiple overlapping trades
        # from the same breakout trend.
        # ---------------------------------------------

        if breakout_result is not None:

            i = j + 1

        else:

            i += 1

    else:

        i += 1

# -----------------------------------------------------
# CALCULATE STRIKE RATE
# -----------------------------------------------------

total_completed_trades = (
    target_yes
    +
    target_no
)

if total_completed_trades > 0:

    strike_rate = (
        target_yes
        /
        total_completed_trades
    ) * 100

else:

    strike_rate = 0

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

# PROCESS ONE STOCK

# =========================================================

def process_stock(symbol, company):

```
try:

    df = download_stock_data(symbol)

    if df is None:

        return None

    # Minimum data required

    minimum_required = (
        ANALYSIS_TRADING_DAYS
        +
        LOOKBACK_DAYS
    )

    if len(df) < minimum_required:

        print(
            f"Insufficient data for {symbol}"
        )

        return None

    # Current market calculations

    current_data = (
        calculate_current_values(df)
    )

    # Historical breakout calculations

    breakout_data = (
        analyse_breakouts(df)
    )

    return {

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

except Exception as e:

    print(
        f"Error processing {symbol}: {e}"
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
print("NIFTY 100 BREAKOUT SCREENER")
print("=" * 70)
print()

# -----------------------------------------------------
# READ NIFTY 100 STOCK LIST
# -----------------------------------------------------

try:

    stocks = pd.read_csv(
        SYMBOL_FILE
    )

except Exception as e:

    print(
        f"Error reading {SYMBOL_FILE}: {e}"
    )

    return

print(
    f"Total stocks to process: {len(stocks)}"
)

print()

results = []

# -----------------------------------------------------
# PROCESS EACH STOCK
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

        results.append(result)

        print(
            f"Close: ₹{result['yesterday_close']}"
        )

        print(
            f"20 Day High: ₹{result['high_20_day']}"
        )

        print(
            f"Away: {result['away_percent']}%"
        )

        print(
            f"Target Yes: {result['target_yes']}"
        )

        print(
            f"Target No: {result['target_no']}"
        )

        print(
            f"Strike Rate: {result['strike_rate']}%"
        )

    # Avoid too many requests at once

    time.sleep(0.3)

# -----------------------------------------------------
# SORT BY STRIKE RATE
# -----------------------------------------------------

results.sort(

    key=lambda x: x["strike_rate"],

    reverse=True
)

# -----------------------------------------------------
# IST TIME
# -----------------------------------------------------

ist_time = datetime.now(
    ZoneInfo("Asia/Kolkata")
)

last_updated = ist_time.strftime(
    "%d-%b-%Y %I:%M %p IST"
)

# -----------------------------------------------------
# FINAL JSON OUTPUT
# -----------------------------------------------------

output = {

    "last_updated":
        last_updated,

    "total_stocks":
        len(results),

    "strategy": {

        "analysis_period":
            "Last 1 year (approximately 252 trading days)",

        "breakout":
            "Fresh 20-day high",

        "target":
            "6% gain from breakout level",

        "target_yes":
            "6% target achieved before new 20-day low",

        "target_no":
            "New 20-day low before 6% target",

        "strike_rate":
            "Target Yes / (Target Yes + Target No) * 100"
    },

    "stocks":
        results
}

# -----------------------------------------------------
# WRITE DATA.JSON
# -----------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        indent=4,
        ensure_ascii=False
    )

# -----------------------------------------------------
# FINAL MESSAGE
# -----------------------------------------------------

print()
print("=" * 70)
print("PROCESS COMPLETED")
print("=" * 70)
print()

print(
    f"Successful stocks: {len(results)}"
)

print(
    f"Last Updated: {last_updated}"
)

print(
    f"Output File: {OUTPUT_FILE}"
)

print()
```

# =========================================================

# START PROGRAM

# =========================================================

if **name** == "**main**":

main()

