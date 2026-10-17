
const foodRows = document.querySelectorAll("#foodTable tbody tr");

const totalDonations = foodRows.length;

const availableFood = document.querySelectorAll(
    "#foodTable .status"
).length;

document.getElementById("totalDonations").textContent =
    totalDonations;

document.getElementById("availableFood").textContent =
    availableFood;

const foodRequestsEl = document.getElementById("foodRequests");\nif (foodRequestsEl) foodRequestsEl.textContent = 0;

const searchInput = document.getElementById("searchInput");

if (searchInput) searchInput.addEventListener("input", function () {
    const searchValue = searchInput.value.toLowerCase();

    foodRows.forEach(function (row) {
        const rowText = row.textContent.toLowerCase();

        if (rowText.includes(searchValue)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
});

