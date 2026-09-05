let stockList = [];


async function loadData() {

    try {

        const response = await fetch(
            "data.json?timestamp=" + new Date().getTime()
        );

        const data = await response.json();

        stockList = data.stocks;

        document.getElementById(
            "totalStocks"
        ).innerText = data.total_stocks;


        document.getElementById(
            "lastUpdated"
        ).innerText = data.last_updated;


        displayStocks(stockList);

    }

    catch (error) {

        console.error(error);

        document.getElementById(
            "stockData"
        ).innerHTML = `

            <tr>

                <td colspan="6">

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


    stocks.forEach(stock => {

        let rowClass = "";

        if (stock.percent_from_high >= -1) {

            rowClass = "very-near";

        }

        else if (stock.percent_from_high >= -3) {

            rowClass = "near-high";

        }

        else if (stock.percent_from_high <= -10) {

            rowClass = "far-high";

        }


        const row = `

            <tr class="${rowClass}">

                <td>
                    ${stock.symbol}
                </td>

                <td>
                    ${stock.company}
                </td>

                <td>
                    ₹ ${stock.latest_close}
                </td>

                <td>
                    ₹ ${stock.high_20_day}
                </td>

                <td>
                    ${stock.high_date}
                </td>

                <td>
                    ${stock.percent_from_high}%
                </td>

            </tr>

        `;


        tableBody.innerHTML += row;

    });

}


document.getElementById(
    "searchBox"
).addEventListener(
    "keyup",
    function() {

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


        displayStocks(filteredStocks);

    }
);


loadData();
