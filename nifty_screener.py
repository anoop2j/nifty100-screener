import pandas as pd
import yfinance as yf
from datetime import datetime
import os
import time

OUTPUT_FILE = "nifty100_20day_high.html"


# ---------------------------------------------
# GET NIFTY 100 STOCKS
# ---------------------------------------------

def get_nifty100_stocks():

    # Official Nifty Indices CSV URL
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"

    try:

        print("Downloading Nifty 100 stock list...")

        df = pd.read_csv(url)

        print("Columns found:")
        print(df.columns.tolist())

        print(f"Total stocks found: {len(df)}")

        return df

    except Exception as e:

        print("ERROR downloading Nifty 100 list:")
        print(e)

        return None


# ---------------------------------------------
# GET STOCK PRICE DATA
# ---------------------------------------------

def get_stock_data(symbol):

    try:

        yahoo_symbol = symbol.strip() + ".NS"

        print(f"Downloading data for {yahoo_symbol}")

        df = yf.download(
            yahoo_symbol,
            period="2mo",
            progress=False,
            auto_adjust=False
        )

        if df.empty:

            print(f"No data found for {symbol}")

            return None

        # Last 20 trading days
        df = df.tail(20)

        high_20_day = float(df["High"].max().iloc[0])

        latest_close = float(df["Close"].iloc[-1].iloc[0])

        latest_high = float(df["High"].iloc[-1].iloc[0])

        high_date = df["High"].idxmax().iloc[0]

        distance = (
            (latest_close - high_20_day)
            / high_20_day
        ) * 100

        return {

            "Symbol": symbol,

            "20 Day High": round(high_20_day, 2),

            "Latest Close": round(latest_close, 2),

            "Latest Day High": round(latest_high, 2),

            "High Date": high_date.strftime("%d-%b-%Y"),

            "% From 20 Day High": round(distance, 2)

        }

    except Exception as e:

        print(f"ERROR processing {symbol}: {e}")

        return None


# ---------------------------------------------
# GENERATE HTML
# ---------------------------------------------

def generate_html_report(df):

    print("Generating HTML report...")

    report_date = datetime.now().strftime(
        "%d-%b-%Y %I:%M %p"
    )

    html = f"""
<!DOCTYPE html>

<html>

<head>

<title>Nifty 100 - 20 Day High Report</title>

<style>

body {{
    font-family: Arial;
    margin: 30px;
    background-color: #f5f5f5;
}}

h1 {{
    color: #003366;
}}

table {{
    border-collapse: collapse;
    width: 100%;
    background: white;
}}

th {{
    background: #003366;
    color: white;
    padding: 10px;
}}

td {{
    padding: 8px;
    border-bottom: 1px solid #ddd;
}}

.near-high {{
    background-color: #d4edda;
}}

</style>

</head>

<body>

<h1>Nifty 100 - Last 20 Trading Day High</h1>

<p>
Report Generated: {report_date}
</p>

<table>

<tr>

<th>Symbol</th>
<th>20 Day High</th>
<th>Latest Close</th>
<th>Latest Day High</th>
<th>High Date</th>
<th>% From High</th>

</tr>
"""

    df = df.sort_values(
        "% From 20 Day High",
        ascending=False
    )

    for _, row in df.iterrows():

        css_class = ""

        if row["% From 20 Day High"] >= -2:
            css_class = "near-high"

        html += f"""

<tr class="{css_class}">

<td>{row['Symbol']}</td>

<td>{row['20 Day High']}</td>

<td>{row['Latest Close']}</td>

<td>{row['Latest Day High']}</td>

<td>{row['High Date']}</td>

<td>{row['% From 20 Day High']}%</td>

</tr>

"""

    html += """

</table>

</body>

</html>

"""

    # Write file
    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

    print("=" * 50)
    print("HTML FILE CREATED SUCCESSFULLY")
    print("File:", OUTPUT_FILE)
    print("Full Path:", os.path.abspath(OUTPUT_FILE))
    print("File Exists:", os.path.exists(OUTPUT_FILE))
    print("=" * 50)


# ---------------------------------------------
# MAIN
# ---------------------------------------------

def main():

    print("=" * 50)
    print("STARTING NIFTY 100 SCREENER")
    print("=" * 50)

    nifty_df = get_nifty100_stocks()

    results = []

    if nifty_df is not None:

        for index, row in nifty_df.iterrows():

            symbol = str(row["Symbol"]).strip()

            print(
                f"\nProcessing "
                f"{index + 1}/{len(nifty_df)} : {symbol}"
            )

            stock_data = get_stock_data(symbol)

            if stock_data:
                results.append(stock_data)

            time.sleep(0.2)

    # IMPORTANT:
    # Generate HTML even if no data is available

    if results:

        result_df = pd.DataFrame(results)

    else:

        print("WARNING: No stock data received.")

        # Create empty dataframe with required columns
        result_df = pd.DataFrame(
            columns=[
                "Symbol",
                "20 Day High",
                "Latest Close",
                "Latest Day High",
                "High Date",
                "% From 20 Day High"
            ]
        )

    # ALWAYS CREATE HTML FILE
    generate_html_report(result_df)


if __name__ == "__main__":

    main()
