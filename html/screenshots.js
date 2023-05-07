document.addEventListener("DOMContentLoaded", () => {
    const images = [
        "images/screenshot1.png",
        "images/screenshot2.png",
        "images/screenshot3.png",
        // Add more images as needed.
    ];

    const screenshot = document.getElementById("screenshot");
    let currentIndex = 0;

    function changeImage() {
        currentIndex++;
        if (currentIndex >= images.length) {
            currentIndex = 0;
        }
        screenshot.src = images[currentIndex];
    }

    screenshot.addEventListener("click", changeImage);

    setInterval(changeImage, 5000); // Change the image every 5 seconds.
});

