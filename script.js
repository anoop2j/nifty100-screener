let stockList = [];


async function loadData() {

    try {

        const response = await fetch(
            "./data.json?v=" +
            new Date().getTime()
        );


        if (!response.ok) {

            throw new Error(
                "Unable to load data.json"
            );

        }


        const data = await response.json();


        stockList = data.stocks || [];


        document.getElementById(
            "totalStocks"
        ).innerText = data.total_stocks || 0;


        document.getElementById(
            "lastUpdated"
        ).innerText =
            data.last_updated ||
            "Not Available";


        displayStocks(stockList);

    }

    catch (error) {

        console.error(error);

        document.getElementById(
            "stockData"
        ).innerHTML = `

        <tr>

            <td colspan="8">

                Error loading stock data.

            </td>

        </tr>

        `;

    }

}


function displayStocks(stocks) {

    const tableBody = document.getElementById(
        "stockData"
    );


    tableBody.innerHTML = "";


    if (stocks.length === 0) {

        tableBody.innerHTML = `

        <tr>

            <td colspan="8">

                No stock data available.

            </td>

        </tr>

        `;

        return;

    }


    stocks.forEach(stock => {

        let rowClass = "";


        // Colour based on distance from 20-day high

        if (stock.away_percent >= -1) {

            rowClass = "very-near";

        }

        else if (stock.away_percent >= -3) {

            rowClass = "near-high";

        }

        else if (stock.away_percent <= -10) {

            rowClass = "far-high";

        }


        const row = document.createElement(
            "tr"
        );


        row.className = rowClass;


        row.innerHTML = `

            <td>

                <strong>
                    ${stock.symbol}
                </strong>

            </td>


            <td>

                ${stock.company}

            </td>


            <td>

                ₹ ${stock.yesterday_close}

            </td>


            <td>

                ₹ ${stock.high_20_day}

            </td>


            <td>

                ${stock.away_percent}%

            </td>


            <td>

                ${stock.target_yes}

            </td>


            <td>

                ${stock.target_no}

            </td>


            <td>

                <strong>

                    ${stock.strike_rate}%

                </strong>

            </td>

        `;


        tableBody.appendChild(row);

    });

}


document.addEventListener(

    "DOMContentLoaded",

    function () {


        const searchBox = document.getElementById(
            "searchBox"
        );


        searchBox.addEventListener(

            "input",

            function () {


                const searchText =
                    this.value.toLowerCase();


                const filteredStocks =

                    stockList.filter(stock =>

                        stock.symbol
                            .toLowerCase()
                            .includes(searchText)

                        ||

                        stock.company
                            .toLowerCase()
                            .includes(searchText)

                    );


                displayStocks(
                    filteredStocks
                );

            }

        );


        loadData();

    }

);
