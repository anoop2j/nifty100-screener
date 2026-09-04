import pandas as pd
import yfinance as yf
from datetime import datetime

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------

INDEX_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"

OUTPUT_FILE = "nifty100_20day_high.html"

# -------------------------------------------------------
# STEP 1 - READ NIFTY 100 STOCK LIST
# -------------------------------------------------------

def get_nifty100_stocks():

    try:

        df = pd.read_csv(INDEX_URL)

        print("Nifty 100 stocks downloaded successfully")

        return df

    except Exception as e:

        print("Error downloading Nifty 100 list:", e)

        return None


# -------------------------------------------------------
# STEP 2 - GET LAST 20 DAY HIGH
# -------------------------------------------------------

def get_stock_data(symbol):

    try:

        # NSE stocks in Yahoo Finance require .NS suffix
        yahoo_symbol = symbol + ".NS"

        stock = yf.Ticker(yahoo_symbol)

        # Download last 40 calendar days
        # This ensures approximately 20 trading days
        df = stock.history(period="1mo")

        if df.empty:

            return None

        # Keep last 20 trading days
        df = df.tail(20)

        high_20_day = df["High"].max()

        latest_close = df["Close"].iloc[-1]

        latest_high = df["High"].iloc[-1]

        distance_from_high = (
            (latest_close - high_20_day)
            / high_20_day
        ) * 100

        return {

            "Symbol": symbol,

            "20 Day High": round(high_20_day, 2),

            "Latest Close": round(latest_close, 2),

            "Latest Day High": round(latest_high, 2),

            "% From 20 Day High":
                round(distance_from_high, 2)

        }

    except Exception as e:

        print(f"Error processing {symbol}: {e}")

        return None


# -------------------------------------------------------
# STEP 3 - PROCESS ALL NIFTY 100 STOCKS
# -------------------------------------------------------

def process_nifty100():

    nifty_df = get_nifty100_stocks()

    if nifty_df is None:

        return

    results = []

    for index, row in nifty_df.iterrows():

        symbol = row["Symbol"]

        company_name = row.get("Company Name", "")

        print(
            f"Processing {index + 1} / "
            f"{len(nifty_df)} : {symbol}"
        )

        data = get_stock_data(symbol)

        if data:

            data["Company Name"] = company_name

            results.append(data)

    return pd.DataFrame(results)


# -------------------------------------------------------
# STEP 4 - GENERATE HTML REPORT
# -------------------------------------------------------

def generate_html_report(df):

    df = df.sort_values(
        by="% From 20 Day High",
        ascending=False
    )

    report_date = datetime.now().strftime(
        "%d-%b-%Y %I:%M %p"
    )

    html = f"""

    <!DOCTYPE html>

    <html>

    <head>

    <title>Nifty 100 - Last 20 Day High Report</title>

    <style>

    body {{

        font-family: Arial, sans-serif;

        background-color: #f4f6f9;

        margin: 30px;

    }}

    h1 {{

        color: #1a237e;

    }}

    .info {{

        color: #555;

        margin-bottom: 20px;

    }}

    table {{

        border-collapse: collapse;

        width: 100%;

        background: white;

    }}

    th {{

        background-color: #1a237e;

        color: white;

        padding: 12px;

        text-align: left;

    }}

    td {{

        padding: 10px;

        border-bottom: 1px solid #ddd;

    }}

    tr:hover {{

        background-color: #f1f1f1;

    }}

    .near-high {{

        background-color: #d4edda;

    }}

    .far-high {{

        background-color: #f8d7da;

    }}

    </style>

    </head>

    <body>

    <h1>Nifty 100 - Last 20 Trading Day High</h1>

    <div class="info">

    Report Generated: {report_date}

    </div>

    """

    html += """

    <table>

    <tr>

        <th>Symbol</th>

        <th>Company Name</th>

        <th>20 Day High</th>

        <th>Latest Close</th>

        <th>Latest Day High</th>

        <th>% From 20 Day High</th>

    </tr>

    """

    for _, row in df.iterrows():

        percentage = row["% From 20 Day High"]

        # Highlight stocks near 20-day high

        if percentage >= -2:

            row_class = "near-high"

        elif percentage <= -10:

            row_class = "far-high"

        else:

            row_class = ""

        html += f"""

        <tr class="{row_class}">

        <td>{row['Symbol']}</td>

        <td>{row['Company Name']}</td>

        <td>{row['20 Day High']}</td>

        <td>{row['Latest Close']}</td>

        <td>{row['Latest Day High']}</td>

        <td>{row['% From 20 Day High']}%</td>

        </tr>

        """

    html += """

    </table>

    </body>

    </html>

    """

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    print(
        f"\nHTML report generated successfully:"
        f"\n{OUTPUT_FILE}"
    )


# -------------------------------------------------------
# MAIN PROGRAM
# -------------------------------------------------------

if __name__ == "__main__":

    print("Starting Nifty 100 Analysis...")

    result_df = process_nifty100()

    if result_df is not None and not result_df.empty:

        generate_html_report(result_df)

    else:

        print("No data generated.")
