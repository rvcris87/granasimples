document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".password-toggle").forEach((botao) => {
        botao.addEventListener("click", () => {
            const campo = botao.parentElement.querySelector("input");
            const mostrar = campo.type === "password";

            campo.type = mostrar ? "text" : "password";
            botao.textContent = mostrar ? "Ocultar" : "Mostrar";
            botao.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
        });
    });
});
