let stockData = [];

async function loadData() {
    try {
        const response = await fetch("data.json?" + new Date().getTime());

        if (!response.ok) {
            throw new Error("Unable to load data.json");
        }

        const data = await response.json();

        // New data.json structure:
        // {
        //   "updated": "...",
        //   "stocks": [...]
        // }

        stockData = Array.isArray(data.stocks) ? data.stocks : [];

        // Updated time
        const updatedElement = document.getElementById("updated");

        if (updatedElement) {
            updatedElement.textContent =
                data.updated || "Not Available";
        }

        // Total stocks
        const totalElement =
            document.getElementById("totalStocks");

        if (totalElement) {
            totalElement.textContent =
                stockData.length;
        }

        // Display table
        displayStocks(stockData);

    } catch (error) {

        console.error("Error loading data:", error);

        const totalElement =
            document.getElementById("totalStocks");

        if (totalElement) {
            totalElement.textContent = "0";
        }

        const updatedElement =
            document.getElementById("updated");

        if (updatedElement) {
            updatedElement.textContent =
                "Unable to load data";
        }
    }
}


function displayStocks(stocks) {

    const tableBody =
        document.getElementById("stockTableBody");

    if (!tableBody) {
        return;
    }

    tableBody.innerHTML = "";

    stocks.forEach(function(stock, index) {

        const row =
            document.createElement("tr");

        const away =
            Number(stock["20 Day High Away %"] || 0);

        const strike =
            Number(stock["Strike Rate"] || 0);

        row.innerHTML = `
            <td>${index + 1}</td>

            <td>
                <strong>
                    ${stock["Stock Code"] || "-"}
                </strong>
            </td>

            <td>
                ${formatNumber(stock["Yesterday Close"])}
            </td>

            <td>
                ${formatNumber(stock["20 Day High"])}
            </td>

            <td>
                ${away.toFixed(2)}%
            </td>

            <td>
                ${stock["Target Met Yes"] ?? 0}
            </td>

            <td>
                ${stock["Target Met No"] ?? 0}
            </td>

            <td>
                ${stock["Pending"] ?? 0}
            </td>

            <td>
                ${strike.toFixed(2)}%
            </td>
        `;

        tableBody.appendChild(row);
    });
}


function formatNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "-";
    }

    const number =
        Number(value);

    if (isNaN(number)) {
        return "-";
    }

    return number.toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    );
}


// ============================================================
// SEARCH
// ============================================================

function searchStocks() {

    const searchInput =
        document.getElementById("searchInput");

    if (!searchInput) {
        return;
    }

    const searchText =
        searchInput.value
            .trim()
            .toUpperCase();

    if (searchText === "") {

        displayStocks(stockData);

        return;
    }

    const filtered =
        stockData.filter(function(stock) {

            const symbol =
                String(
                    stock["Stock Code"] || ""
                ).toUpperCase();

            return symbol.includes(searchText);
        });

    displayStocks(filtered);
}


// ============================================================
// SORT BY 20 DAY HIGH AWAY %
// ============================================================

function sortByAway() {

    const sorted =
        [...stockData].sort(
            function(a, b) {

                return Number(
                    a["20 Day High Away %"] || 0
                ) -
                Number(
                    b["20 Day High Away %"] || 0
                );
            }
        );

    displayStocks(sorted);
}


// ============================================================
// INITIAL LOAD
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        loadData();

        const searchInput =
            document.getElementById(
                "searchInput"
            );

        if (searchInput) {

            searchInput.addEventListener(
                "input",
                searchStocks
            );
        }
    }
);
