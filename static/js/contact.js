
document.getElementById("contactForm").addEventListener("submit", function(event) {
    event.preventDefault();

    document.getElementById("contact-status").textContent =
        "Thank you! Your message has been entered successfully.";

    this.reset();
});
