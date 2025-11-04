// Typing Animation Script
const textToType = "FraudHive - Network Intelligence Platform";
const typingSpeed = 120; // milliseconds per character
const deletingSpeed = 50; // milliseconds per character when deleting
const pauseBeforeDelete = 2000; // pause at end before deleting
const pauseBeforeRetype = 1000; // pause before retyping
const typingElement = document.getElementById('typingText');

let charIndex = 0;
let isDeleting = false;
let isPaused = false;

function typeText() {
    if (!isDeleting && charIndex < textToType.length) {
        // Typing forward
        typingElement.textContent = textToType.substring(0, charIndex + 1);
        charIndex++;
        setTimeout(typeText, typingSpeed);
    } else if (!isDeleting && charIndex === textToType.length) {
        // Reached end, pause then start deleting
        if (!isPaused) {
            isPaused = true;
            setTimeout(() => {
                isDeleting = true;
                isPaused = false;
                typeText();
            }, pauseBeforeDelete);
        }
    } else if (isDeleting && charIndex > 0) {
        // Deleting backward
        charIndex--;
        typingElement.textContent = textToType.substring(0, charIndex);
        setTimeout(typeText, deletingSpeed);
    } else if (isDeleting && charIndex === 0) {
        // Finished deleting, pause then start retyping
        isDeleting = false;
        setTimeout(typeText, pauseBeforeRetype);
    }
}

// Alternative: Type once and stop (no loop)
function typeTextOnce() {
    if (charIndex < textToType.length) {
        typingElement.textContent = textToType.substring(0, charIndex + 1);
        charIndex++;
        setTimeout(typeTextOnce, typingSpeed);
    } else {
        // Hide cursor after typing completes
        setTimeout(() => {
            document.querySelector('.typing-cursor').style.display = 'none';
        }, 1000);
    }
}

// Start typing animation on page load
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        typeTextOnce(); // Use typeTextOnce() for single typing, or typeText() for loop
    }, 500); // Small delay before starting
});
