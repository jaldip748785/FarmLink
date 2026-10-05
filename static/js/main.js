/* ==========================================
   FarmLink - Main JavaScript
========================================== */

document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // Auto Close Alerts
    // ==========================================
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.classList.add("fade");

            setTimeout(function () {
                alert.remove();
            }, 500);

        }, 4000);
    });


    // ==========================================
    // Scroll To Top Button
    // ==========================================
    const topBtn = document.getElementById("scrollTopBtn");

    if (topBtn) {

        window.addEventListener("scroll", function () {

            if (window.scrollY > 300) {
                topBtn.style.display = "block";
            } else {
                topBtn.style.display = "none";
            }

        });

        topBtn.addEventListener("click", function () {

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });

        });
    }


    // ==========================================
    // Confirm Delete
    // ==========================================
    const deleteButtons = document.querySelectorAll(".delete-btn");

    deleteButtons.forEach(function (button) {

        button.addEventListener("click", function (e) {

            const confirmDelete = confirm("Are you sure you want to delete this item?");

            if (!confirmDelete) {
                e.preventDefault();
            }

        });

    });


    // ==========================================
    // Image Preview
    // ==========================================
    const imageInput = document.getElementById("image");
    const preview = document.getElementById("imagePreview");

    if (imageInput && preview) {

        imageInput.addEventListener("change", function () {

            const file = this.files[0];

            if (file) {

                const reader = new FileReader();

                reader.onload = function (e) {
                    preview.src = e.target.result;
                    preview.style.display = "block";
                };

                reader.readAsDataURL(file);

            }

        });

    }


    // ==========================================
    // Password Show / Hide
    // ==========================================
    const togglePassword = document.querySelectorAll(".toggle-password");

    togglePassword.forEach(function (button) {

        button.addEventListener("click", function () {

            const input = document.getElementById(button.dataset.target);

            if (!input) return;

            if (input.type === "password") {
                input.type = "text";
                button.innerHTML = "Hide";
            } else {
                input.type = "password";
                button.innerHTML = "Show";
            }

        });

    });


    // ==========================================
    // Loading Button
    // ==========================================
    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener("submit", function () {

            const btn = form.querySelector("button[type='submit']");

            if (btn) {

                btn.disabled = true;

                btn.innerHTML =
                    '<span class="spinner-border spinner-border-sm me-2"></span> Please Wait...';

            }

        });

    });


    // ==========================================
    // Smooth Scroll
    // ==========================================
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {

        anchor.addEventListener("click", function (e) {

            const target = document.querySelector(this.getAttribute("href"));

            if (target) {

                e.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth"
                });

            }

        });

    });

});


// ==========================================
// Show Bootstrap Toast
// ==========================================
function showToast(message) {

    alert(message);

}


// ==========================================
// Format Currency
// ==========================================
function formatPrice(price) {

    return "₹ " + parseFloat(price).toFixed(2);

}


// ==========================================
// Logout Confirmation Modal
// ==========================================
// Modal is triggered via data-bs-toggle and data-bs-target attributes
// No additional JavaScript needed for basic functionality



// ==========================================
// Copy Text
// ==========================================
function copyText(text) {

    navigator.clipboard.writeText(text);

    alert("Copied Successfully!");

}


// ==========================================
// Number Only Input
// ==========================================
function onlyNumbers(event) {

    const key = event.key;

    if (!/[0-9]/.test(key) &&
        key !== "Backspace" &&
        key !== "Delete" &&
        key !== "ArrowLeft" &&
        key !== "ArrowRight") {

        event.preventDefault();

    }

}


// ==========================================
// Toggle Element
// ==========================================
function toggleElement(id) {

    const element = document.getElementById(id);

    if (!element) return;

    if (element.style.display === "none") {
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }

}