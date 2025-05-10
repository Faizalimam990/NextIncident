// scripts.js

// Animate Navbar on Load
gsap.from(".navbar", {
    duration: 1,
    y: -100,
    opacity: 0,
    ease: "bounce"
});

// Animate Footer on Load
gsap.from(".footer", {
    duration: 1,
    y: 100,
    opacity: 0,
    ease: "power1.out",
    delay: 0.5
});

// Animate Main Content
gsap.from(".container", {
    duration: 1,
    opacity: 0,
    y: 50,
    ease: "power2.out",
    delay: 0.3
});
