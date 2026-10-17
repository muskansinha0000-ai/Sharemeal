
document.getElementById("donationForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const donor = document.getElementById("donor").value;
    const food = document.getElementById("food").value;
    const quantity = document.getElementById("quantity").value;

    document.getElementById("message").textContent =
        "Thank you, " + donor + "! Your donation of " +
        quantity + " servings of " + food +
        " has been entered successfully.";

    this.reset();
});
