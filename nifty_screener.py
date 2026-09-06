import pandas as pd
import yfinance as yf
import json
import time
from datetime import datetime

# =========================================================

# CONFIGURATION

# =========================================================

SYMBOL_FILE = "nifty100_symbols.csv"
OUTPUT_FILE = "data.json"

TARGET_PERCENT = 6
LOOKBACK_DAYS = 20
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
        subset=["High", "Low", "Close"]
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

1. Yesterday/latest available close
2. Current 20-day high
3. Percentage away from 20-day high
"""


recent_df = df.tail(LOOKBACK_DAYS)


high_20_day = recent_df["High"].max()


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
```

# =========================================================

# CHECK FOR NEW 20-DAY LOW

# =========================================================

def is_new_20_day_low(df, index):

```
"""
Returns True if the Low price on the current day
is lower than the lowest Low of the previous 20
trading days.
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


if current_low < previous_20_low:

    return True


return False
```

# =========================================================

# ANALYSE BREAKOUT STRATEGY

# =========================================================

def analyse_breakouts(df):

```
"""
Strategy:

STEP 1
Detect a fresh 20-day high breakout.

STEP 2
Breakout target = previous 20-day high + 6%.

STEP 3
After breakout, monitor future prices.

SUCCESS:
Price achieves 6% target before making a new
20-day low.

FAILURE:
Price creates a new 20-day low before achieving
the 6% target.

PENDING:
Neither event occurs before the end of the
one-year analysis period.

Pending signals are not included in strike rate.
"""


target_yes = 0

target_no = 0

pending = 0


# -----------------------------------------------------
# Keep enough historical data before one-year period
# so that 20-day calculations are accurate.
# -----------------------------------------------------

required_days = (

    ANALYSIS_TRADING_DAYS
    +
    LOOKBACK_DAYS

)


analysis_df = df.tail(
    required_days
).copy()


# -----------------------------------------------------
# Track whether stock is currently in breakout trend.
#
# This prevents counting consecutive new highs
# as multiple separate breakout signals.
# -----------------------------------------------------

breakout_active = False


# Start after first 20 trading days

for i in range(
    LOOKBACK_DAYS,
    len(analysis_df)
):


    # -------------------------------------------------
    # PREVIOUS 20-DAY HIGH
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


    current_low = (

        analysis_df["Low"]
        .iloc[i]

    )


    # -------------------------------------------------
    # DETERMINE IF CURRENT DAY IS BELOW 20-DAY HIGH
    #
    # This resets the breakout state and allows
    # a future fresh breakout.
    # -------------------------------------------------

    if current_high <= previous_20_high:

        breakout_active = False


    # -------------------------------------------------
    # DETECT FRESH 20-DAY HIGH BREAKOUT
    # -------------------------------------------------

    if (

        current_high > previous_20_high

        and

        breakout_active is False

    ):


        breakout_active = True


        breakout_price = (
            previous_20_high
        )


        target_price = (

            breakout_price

            * (1 + TARGET_PERCENT / 100)

        )


        breakout_result = None


        # -------------------------------------------------
        # MONITOR SUBSEQUENT DAYS
        # -------------------------------------------------

        for j in range(
            i + 1,
            len(analysis_df)
        ):


            future_high = (

                analysis_df["High"]
                .iloc[j]

            )


            # ---------------------------------------------
            # CONDITION 1:
            # CHECK IF 6% TARGET IS ACHIEVED
            # ---------------------------------------------

            if future_high >= target_price:


                breakout_result = "YES"

                break


            # ---------------------------------------------
            # CONDITION 2:
            # CHECK IF NEW 20-DAY LOW IS CREATED
            # ---------------------------------------------

            if is_new_20_day_low(
                analysis_df,
                j
            ):


                breakout_result = "NO"

                break


        # -------------------------------------------------
        # UPDATE BREAKOUT COUNTERS
        # -------------------------------------------------

        if breakout_result == "YES":


            target_yes += 1


        elif breakout_result == "NO":


            target_no += 1


        else:


            # Neither target nor new 20-day low
            # occurred during analysis period.

            pending += 1


# -----------------------------------------------------
# CALCULATE STRIKE RATE
# -----------------------------------------------------

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


# -----------------------------------------------------
# RETURN RESULTS
# -----------------------------------------------------

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

def process_stock(symbol, company):

```
try:


    # Download historical data

    df = download_stock_data(
        symbol
    )


    if df is None:


        return None


    # Ensure sufficient historical data

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
    # CURRENT MARKET VALUES
    # -------------------------------------------------

    current_data = (

        calculate_current_values(
            df
        )

    )


    # -------------------------------------------------
    # BREAKOUT PERFORMANCE ANALYSIS
    # -------------------------------------------------

    breakout_data = (

        analyse_breakouts(
            df
        )

    )


    # -------------------------------------------------
    # RETURN STOCK RESULT
    # -------------------------------------------------

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

print("=" * 65)

print(
    "NIFTY 100 BREAKOUT & STRIKE RATE SCREENER"
)

print("=" * 65)

print()


# -----------------------------------------------------
# READ NIFTY 100 SYMBOL LIST
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

print("-" * 65)


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


    if result:


        results.append(
            result
        )


        print(

            f"  Close: ₹{result['yesterday_close']}"

        )


        print(

            f"  20D High: ₹{result['high_20_day']}"

        )


        print(

            f"  Away: {result['away_percent']}%"

        )


        print(

            f"  Target Yes: {result['target_yes']}"

        )


        print(

            f"  Target No: {result['target_no']}"

        )


        print(

            f"  Strike Rate: "

            f"{result['strike_rate']}%"

        )


    # Small delay to avoid excessive requests

    time.sleep(0.3)


# -----------------------------------------------------
# SORT RESULTS
#
# Primary: Highest Strike Rate
# Secondary: Closest to 20-Day High
# -----------------------------------------------------

results.sort(

    key=lambda x: (

        x["strike_rate"],

        x["away_percent"]

    ),

    reverse=True

)


# -----------------------------------------------------
# CREATE FINAL OUTPUT
# -----------------------------------------------------

output = {


   "last_updated":

    datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime(
        "%d-%b-%Y %I:%M %p IST"
    ),


    "total_stocks":

        len(results),


    "strategy": {


        "breakout":

            "Fresh 20-day high breakout",


        "target":

            "6 percent above breakout level",


        "failure":

            "New 20-day low before target",


        "period":

            "Last 1 year",


        "strike_rate_formula":

            "Target Yes / (Target Yes + Target No) * 100"

    },


    "stocks":

        results

}


# -----------------------------------------------------
# WRITE JSON FILE
# -----------------------------------------------------

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


# -----------------------------------------------------
# SUMMARY
# -----------------------------------------------------

print()

print("=" * 65)

print("PROCESS COMPLETED")

print("=" * 65)

print()

print(

    f"Successful stocks processed: {len(results)}"

)


print(

    f"Output file: {OUTPUT_FILE}"

)


print()

print("=" * 65)
```

# =========================================================

# PROGRAM ENTRY POINT

# =========================================================

if **name** == "**main**":

```
main()
```
