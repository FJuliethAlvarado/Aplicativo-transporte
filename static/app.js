// ===== TRANSICIÓN ENTRE PÁGINAS =====
function goTo(url) {
    document.body.classList.add("fade-out");

    setTimeout(() => {
        window.location.href = url;
    }, 350);
}

// aplicar fade-in al cargar
window.addEventListener("load", () => {
    document.body.classList.add("fade-in");
});