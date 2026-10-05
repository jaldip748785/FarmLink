/* ==========================================
   FarmLink - Search & Filter JavaScript
========================================== */

document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // Live Product Search
    // ==========================================
    const searchInput = document.getElementById("searchInput");
    const productCards = document.querySelectorAll(".product-card");

    if (searchInput) {

        searchInput.addEventListener("keyup", function () {

            const keyword = this.value.toLowerCase();

            productCards.forEach(function (card) {

                const name = card.dataset.name.toLowerCase();

                if (name.includes(keyword)) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }

            });

            checkNoResults();

        });

    }


    // ==========================================
    // Category Filter
    // ==========================================
    const categoryFilter = document.getElementById("categoryFilter");

    if (categoryFilter) {

        categoryFilter.addEventListener("change", function () {

            const category = this.value.toLowerCase();

            productCards.forEach(function (card) {

                if (
                    category === "" ||
                    card.dataset.category.toLowerCase() === category
                ) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }

            });

            checkNoResults();

        });

    }


    // ==========================================
    // District Filter
    // ==========================================
    const districtFilter = document.getElementById("districtFilter");

    if (districtFilter) {

        districtFilter.addEventListener("change", function () {

            const district = this.value.toLowerCase();

            productCards.forEach(function (card) {

                if (
                    district === "" ||
                    card.dataset.district.toLowerCase() === district
                ) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }

            });

            checkNoResults();

        });

    }


    // ==========================================
    // Taluka Filter
    // ==========================================
    const talukaFilter = document.getElementById("talukaFilter");

    if (talukaFilter) {

        talukaFilter.addEventListener("change", function () {

            const taluka = this.value.toLowerCase();

            productCards.forEach(function (card) {

                if (
                    taluka === "" ||
                    card.dataset.taluka.toLowerCase() === taluka
                ) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }

            });

            checkNoResults();

        });

    }


    // ==========================================
    // Village Filter
    // ==========================================
    const villageFilter = document.getElementById("villageFilter");

    if (villageFilter) {

        villageFilter.addEventListener("change", function () {

            const village = this.value.toLowerCase();

            productCards.forEach(function (card) {

                if (
                    village === "" ||
                    card.dataset.village.toLowerCase() === village
                ) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }

            });

            checkNoResults();

        });

    }


    // ==========================================
    // Price Range Filter
    // ==========================================
    const minPrice = document.getElementById("minPrice");
    const maxPrice = document.getElementById("maxPrice");

    function filterPrice() {

        if (!minPrice || !maxPrice) return;

        const min = parseFloat(minPrice.value) || 0;
        const max = parseFloat(maxPrice.value) || Number.MAX_VALUE;

        productCards.forEach(function (card) {

            const price = parseFloat(card.dataset.price);

            if (price >= min && price <= max) {
                card.style.display = "";
            } else {
                card.style.display = "none";
            }

        });

        checkNoResults();

    }

    if (minPrice) minPrice.addEventListener("input", filterPrice);
    if (maxPrice) maxPrice.addEventListener("input", filterPrice);


    // ==========================================
    // Clear Filters
    // ==========================================
    const clearBtn = document.getElementById("clearFilters");

    if (clearBtn) {

        clearBtn.addEventListener("click", function () {

            if (searchInput) searchInput.value = "";
            if (categoryFilter) categoryFilter.value = "";
            if (districtFilter) districtFilter.value = "";
            if (talukaFilter) talukaFilter.value = "";
            if (villageFilter) villageFilter.value = "";
            if (minPrice) minPrice.value = "";
            if (maxPrice) maxPrice.value = "";

            productCards.forEach(function (card) {
                card.style.display = "";
            });

            checkNoResults();

        });

    }


    // ==========================================
    // No Results Message
    // ==========================================
    function checkNoResults() {

        const noResult = document.getElementById("noResults");

        if (!noResult) return;

        let visible = 0;

        productCards.forEach(function (card) {

            if (card.style.display !== "none") {
                visible++;
            }

        });

        if (visible === 0) {
            noResult.style.display = "block";
        } else {
            noResult.style.display = "none";
        }

    }

});


// ==========================================
// Search Form Validation
// ==========================================
function validateSearch() {

    const search = document.getElementById("searchInput");

    if (!search) return true;

    if (search.value.trim() === "") {

        alert("Please enter a product name.");

        search.focus();

        return false;
    }

    return true;

}


// ==========================================
// Reset Search Box
// ==========================================
function resetSearch() {

    const search = document.getElementById("searchInput");

    if (search) {
        search.value = "";
    }

}


// ==========================================
// Sort Products
// ==========================================
function sortProducts(select) {

    const container = document.getElementById("productContainer");

    if (!container) return;

    const cards = Array.from(container.querySelectorAll(".product-card"));

    if (select.value === "low") {

        cards.sort((a, b) =>
            parseFloat(a.dataset.price) - parseFloat(b.dataset.price)
        );

    } else if (select.value === "high") {

        cards.sort((a, b) =>
            parseFloat(b.dataset.price) - parseFloat(a.dataset.price)
        );

    } else {

        cards.sort((a, b) =>
            a.dataset.name.localeCompare(b.dataset.name)
        );

    }

    container.innerHTML = "";

    cards.forEach(function (card) {
        container.appendChild(card);
    });

}