
document.getElementById("requestForm").addEventListener("submit", function(event) {
    event.preventDefault();

    document.getElementById("request-message").textContent =
        "Your food request has been entered successfully!";

    this.reset();
});
