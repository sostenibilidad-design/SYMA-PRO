document.addEventListener("DOMContentLoaded", () => {
    const toggles = document.querySelectorAll(".togglePassword");

    toggles.forEach(toggle => {
        toggle.addEventListener("click", () => {
            const inputId = toggle.getAttribute("data-target"); // lee el input a controlar
            const passwordInput = document.getElementById(inputId);

            const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
            passwordInput.setAttribute("type", type);

            // animación
            toggle.classList.add("icon-animate");

            if (type === "text") {
                toggle.classList.remove("fa-eye-slash");
                toggle.classList.add("fa-eye");
            } else {
                toggle.classList.remove("fa-eye");
                toggle.classList.add("fa-eye-slash");
            }

            // quitar animación después del efecto
            setTimeout(() => {
                toggle.classList.remove("icon-animate");
            }, 400);
        });
    });
});
