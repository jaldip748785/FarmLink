/* ==========================================
   FarmLink - Validation JavaScript
========================================== */

document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // Registration Form Validation
    // ==========================================
    const registerForm = document.getElementById("registerForm");

    if (registerForm) {

        registerForm.addEventListener("submit", function (e) {

            if (!validateRegister()) {
                e.preventDefault();
            }

        });

    }


    // ==========================================
    // Login Form Validation
    // ==========================================
    const loginForm = document.getElementById("loginForm");

    if (loginForm) {

        loginForm.addEventListener("submit", function (e) {

            if (!validateLogin()) {
                e.preventDefault();
            }

        });

    }


    // ==========================================
    // Product Form Validation
    // ==========================================
    const productForm = document.getElementById("productForm");

    if (productForm) {

        productForm.addEventListener("submit", function (e) {

            if (!validateProduct()) {
                e.preventDefault();
            }

        });

    }


    // ==========================================
    // Profile Form Validation
    // ==========================================
    const profileForm = document.getElementById("profileForm");

    if (profileForm) {

        profileForm.addEventListener("submit", function (e) {

            if (!validateProfile()) {
                e.preventDefault();
            }

        });

    }

});


// ==========================================
// Login Validation
// ==========================================
function validateLogin() {

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (email === "") {
        alert("Email is required.");
        return false;
    }

    if (!validateEmail(email)) {
        alert("Enter a valid email.");
        return false;
    }

    if (password === "") {
        alert("Password is required.");
        return false;
    }

    return true;
}


// ==========================================
// Registration Validation
// ==========================================
function validateRegister() {

    const fullName = document.getElementById("full_name").value.trim();
    const mobile = document.getElementById("mobile").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;

    if (fullName.length < 3) {
        alert("Enter your full name.");
        return false;
    }

    if (!validateMobile(mobile)) {
        alert("Enter a valid mobile number.");
        return false;
    }

    if (!validateEmail(email)) {
        alert("Enter a valid email.");
        return false;
    }

    if (!validatePassword(password)) {
        return false;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return false;
    }

    return true;
}


// ==========================================
// Product Validation
// ==========================================
function validateProduct() {

    const name = document.getElementById("name").value.trim();
    const category = document.getElementById("category").value;
    const quantity = document.getElementById("quantity").value;
    const price = document.getElementById("price").value;

    if (name === "") {
        alert("Product name is required.");
        return false;
    }

    if (category === "") {
        alert("Select a category.");
        return false;
    }

    if (quantity === "" || parseFloat(quantity) <= 0) {
        alert("Enter a valid quantity.");
        return false;
    }

    if (price === "" || parseFloat(price) <= 0) {
        alert("Enter a valid price.");
        return false;
    }

    return true;
}


// ==========================================
// Profile Validation
// ==========================================
function validateProfile() {

    const fullName = document.getElementById("full_name").value.trim();
    const mobile = document.getElementById("mobile").value.trim();

    if (fullName.length < 3) {
        alert("Enter your full name.");
        return false;
    }

    if (!validateMobile(mobile)) {
        alert("Invalid mobile number.");
        return false;
    }

    return true;
}


// ==========================================
// Email Validation
// ==========================================
function validateEmail(email) {

    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    return pattern.test(email);

}


// ==========================================
// Mobile Validation
// ==========================================
function validateMobile(mobile) {

    const pattern = /^[6-9]\d{9}$/;

    return pattern.test(mobile);

}


// ==========================================
// Password Validation
// ==========================================
function validatePassword(password) {

    if (password.length < 8) {
        alert("Password must contain at least 8 characters.");
        return false;
    }

    return true;

}


// ==========================================
// Only Numbers
// ==========================================
function onlyNumber(event) {

    const key = event.key;

    if (
        !/[0-9]/.test(key) &&
        key !== "Backspace" &&
        key !== "Delete" &&
        key !== "ArrowLeft" &&
        key !== "ArrowRight" &&
        key !== "Tab"
    ) {
        event.preventDefault();
    }

}


// ==========================================
// Password Strength Indicator
// ==========================================
function passwordStrength(password) {

    const strength = document.getElementById("passwordStrength");

    if (!strength) return;

    if (password.length < 6) {

        strength.innerHTML = "Weak";
        strength.style.color = "red";

    } else if (password.length < 10) {

        strength.innerHTML = "Medium";
        strength.style.color = "orange";

    } else {

        strength.innerHTML = "Strong";
        strength.style.color = "green";

    }

}


// ==========================================
// Image Validation
// ==========================================
function validateImage(input) {

    if (!input.files.length) return true;

    const file = input.files[0];

    const allowed = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    ];

    if (!allowed.includes(file.type)) {

        alert("Only JPG, JPEG, PNG and WEBP images are allowed.");

        input.value = "";

        return false;
    }

    if (file.size > 2 * 1024 * 1024) {

        alert("Image size must be less than 2 MB.");

        input.value = "";

        return false;
    }

    return true;

}


// ==========================================
// Confirm Delete
// ==========================================
function confirmDelete() {

    return confirm("Are you sure you want to delete this record?");

}


// ==========================================
// Logout Confirmation Modal
// ==========================================
// Modal is triggered via data-bs-toggle and data-bs-target attributes
// No additional JavaScript needed for basic functionality
