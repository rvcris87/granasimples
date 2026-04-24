/**
 * prevenir-duplo-clique.js
 * Evita submissão duplicada de formulários ao clicar múltiplas vezes
 */

document.addEventListener('DOMContentLoaded', () => {
    // Evitar clique duplo na criação de meta
    const formCriarMeta = document.querySelector('.form-criar-meta');
    if (formCriarMeta) {
        formCriarMeta.addEventListener('submit', function (e) {
            const btnSubmit = this.querySelector('button[type="submit"]');
            if (btnSubmit) {
                btnSubmit.disabled = true;
                btnSubmit.textContent = 'Criando...';
                btnSubmit.style.opacity = '0.6';
                btnSubmit.style.cursor = 'not-allowed';
            }
        });
    }

    // Evitar clique duplo nos formulários inline de metas
    const metaForms = document.querySelectorAll('.meta-form-inline');
    metaForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const btnSubmit = this.querySelector('button[type="submit"]');
            if (btnSubmit) {
                btnSubmit.disabled = true;
                btnSubmit.style.opacity = '0.6';
                btnSubmit.style.cursor = 'not-allowed';
            }
        });
    });

    // Reabilitar botões se o usuário voltar (navegação)
    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            const buttons = document.querySelectorAll('button[disabled]');
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
                if (btn.textContent === 'Criando...') {
                    btn.textContent = 'Criar Meta';
                }
            });
        }
    });
});
