document.addEventListener("DOMContentLoaded", () => {
    const formatarMoeda = new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
    const chartInstances = [];
    const secoesValidas = Array.from(document.querySelectorAll("[data-section]"))
        .map((secao) => secao.dataset.section);

    function cssVar(nome, fallback) {
        return getComputedStyle(document.documentElement).getPropertyValue(nome).trim() || fallback;
    }

    function chartColors() {
        return {
            text: cssVar("--muted", "#64748b"),
            green: cssVar("--green", "#22c55e"),
            petrol: cssVar("--petrol", "#0e7490"),
            red: cssVar("--red", "#ef4444"),
            violet: cssVar("--violet", "#7c3aed"),
            blue: cssVar("--blue", "#2563eb"),
            grid: document.documentElement.dataset.theme === "dark"
                ? "rgba(226,232,240,0.08)"
                : "rgba(15,23,42,0.08)"
        };
    }

    function mostrarAvisoGrafico(canvas, mensagem) {
        if (!canvas || !canvas.parentElement) return;

        canvas.style.display = "none";

        const avisoExistente = canvas.parentElement.querySelector(".grafico-aviso");
        if (avisoExistente) {
            avisoExistente.textContent = mensagem;
            return;
        }

        const aviso = document.createElement("p");
        aviso.className = "grafico-aviso";
        aviso.textContent = mensagem;
        canvas.parentElement.appendChild(aviso);
    }

    function lerJsonDataset(elemento, chave, valorPadrao = []) {
        try {
            return JSON.parse(elemento.dataset[chave] || JSON.stringify(valorPadrao));
        } catch (erro) {
            console.error(`Erro ao ler dataset ${chave}:`, erro);
            return valorPadrao;
        }
    }

    function registrarGrafico(canvas) {
        const chart = Chart.getChart(canvas);
        if (chart) chartInstances.push(chart);
    }

    function ativarSecao(idSecao) {
        const idSeguro = secoesValidas.includes(idSecao) ? idSecao : "visao-geral";

        document.querySelectorAll("[data-section]").forEach((secao) => {
            secao.classList.toggle("is-active", secao.dataset.section === idSeguro);
        });

        document.querySelectorAll("[data-section-link]").forEach((link) => {
            const ativo = link.dataset.sectionLink === idSeguro;
            link.classList.toggle("ativo", ativo);
            if (ativo) {
                link.setAttribute("aria-current", "page");
            } else {
                link.removeAttribute("aria-current");
            }
        });

        window.setTimeout(() => {
            chartInstances.forEach((chart) => chart.resize());
            window.dispatchEvent(new Event("resize"));
        }, 80);
    }

    function inicializarNavegacaoInterna() {
        const hashInicial = window.location.hash.replace("#", "");
        ativarSecao(hashInicial || "visao-geral");

        document.querySelectorAll("[data-section-link]").forEach((link) => {
            link.addEventListener("click", () => {
                ativarSecao(link.dataset.sectionLink);
            });
        });

        window.addEventListener("hashchange", () => {
            ativarSecao(window.location.hash.replace("#", ""));
        });
    }

    function inicializarGraficoResumo() {
        const dadosGraficos = document.getElementById("dados-graficos");
        const canvasResumo = document.getElementById("graficoResumo");
        const canvasCategorias = document.getElementById("graficoCategorias");

        if (!dadosGraficos) return;

        const totalEntradas = parseFloat(dadosGraficos.dataset.entradas || 0);
        const totalSaidas = parseFloat(dadosGraficos.dataset.saidas || 0);
        const categoriasLabels = lerJsonDataset(dadosGraficos, "categoriasLabels");
        const categoriasValores = lerJsonDataset(dadosGraficos, "categoriasValores");
        const cores = chartColors();

        if (typeof Chart === "undefined") {
            mostrarAvisoGrafico(canvasResumo, "Não foi possível carregar os gráficos agora.");
            mostrarAvisoGrafico(canvasCategorias, "Não foi possível carregar os gráficos agora.");
            return;
        }

        if (canvasResumo) {
            const resumoSemDados = totalEntradas === 0 && totalSaidas === 0;

            new Chart(canvasResumo, {
                type: "doughnut",
                data: {
                    labels: resumoSemDados ? ["Sem dados"] : ["Entradas", "Saídas"],
                    datasets: [{
                        data: resumoSemDados ? [1] : [totalEntradas, totalSaidas],
                        backgroundColor: resumoSemDados ? ["#94a3b8"] : [cores.green, cores.red],
                        borderWidth: 0,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "64%",
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                color: cores.text,
                                boxWidth: 16,
                                padding: 16,
                                font: { size: 13, weight: "700" }
                            }
                        }
                    }
                }
            });
            registrarGrafico(canvasResumo);
        }

        if (!canvasCategorias) return;

        const semDados = !categoriasLabels.length || !categoriasValores.length;
        if (semDados) {
            mostrarAvisoGrafico(canvasCategorias, "Nenhum gasto por categoria neste período.");
            return;
        }

        new Chart(canvasCategorias, {
            type: "bar",
            data: {
                labels: categoriasLabels,
                datasets: [{
                    label: "Gastos por categoria",
                    data: categoriasValores,
                    backgroundColor: [
                        cores.blue,
                        cores.green,
                        "#f59e0b",
                        cores.red,
                        cores.violet,
                        cores.petrol,
                        "#fb7185",
                        "#94a3b8",
                        "#c084fc"
                    ],
                    borderRadius: 12,
                    borderSkipped: false,
                    maxBarThickness: 44
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => formatarMoeda.format(Number(context.raw || 0))
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: cores.text,
                            callback: (value) => formatarMoeda.format(Number(value || 0))
                        },
                        grid: { color: cores.grid }
                    },
                    y: {
                        ticks: {
                            color: cores.text,
                            font: { size: 13, weight: "700" }
                        },
                        grid: { display: false }
                    }
                }
            }
        });
        registrarGrafico(canvasCategorias);
    }

    function inicializarGraficoTendencia() {
        const dadosTendencia = document.getElementById("dados-tendencia");
        const canvasTendencia = document.getElementById("graficoTendencia");

        if (!dadosTendencia || !canvasTendencia) return;

        if (typeof Chart === "undefined") {
            mostrarAvisoGrafico(canvasTendencia, "Não foi possível carregar o gráfico de tendência agora.");
            return;
        }

        const cores = chartColors();
        const tendenciaLabels = lerJsonDataset(dadosTendencia, "evolucaoLabels", lerJsonDataset(dadosTendencia, "labels"));
        const tendenciaEntradas = lerJsonDataset(dadosTendencia, "evolucaoEntradas", lerJsonDataset(dadosTendencia, "entradas"));
        const tendenciaSaidas = lerJsonDataset(dadosTendencia, "evolucaoSaidas", lerJsonDataset(dadosTendencia, "saidas"));
        const tendenciaSaldo = lerJsonDataset(dadosTendencia, "evolucaoSaldo", lerJsonDataset(dadosTendencia, "saldo"));

        const dadosValidos = tendenciaLabels.length
            && tendenciaLabels.length === tendenciaEntradas.length
            && tendenciaLabels.length === tendenciaSaidas.length
            && tendenciaLabels.length === tendenciaSaldo.length;
        const semDados = dadosValidos
            && [...tendenciaEntradas, ...tendenciaSaidas, ...tendenciaSaldo]
                .every((valor) => Number(valor || 0) === 0);

        if (!dadosValidos) {
            mostrarAvisoGrafico(canvasTendencia, "Não foi possível ler os dados da tendência agora.");
            return;
        }

        if (semDados) {
            mostrarAvisoGrafico(canvasTendencia, "Nenhuma movimentação nos últimos 6 meses deste período.");
            return;
        }

        new Chart(canvasTendencia, {
            type: "line",
            data: {
                labels: tendenciaLabels,
                datasets: [
                    {
                        label: "Entradas",
                        data: tendenciaEntradas,
                        borderColor: cores.green,
                        backgroundColor: "rgba(34, 197, 94, 0.12)",
                        tension: 0.42,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: cores.green,
                        pointHoverRadius: 7
                    },
                    {
                        label: "Saídas",
                        data: tendenciaSaidas,
                        borderColor: cores.red,
                        backgroundColor: "rgba(239, 68, 68, 0.1)",
                        tension: 0.42,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: cores.red,
                        pointHoverRadius: 7
                    },
                    {
                        label: "Saldo",
                        data: tendenciaSaldo,
                        borderColor: cores.blue,
                        backgroundColor: "rgba(37, 99, 235, 0.1)",
                        tension: 0.42,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: cores.blue,
                        pointHoverRadius: 7
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: cores.text,
                            padding: 14,
                            font: { size: 13, weight: "700" }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.dataset.label}: ${formatarMoeda.format(Number(context.raw || 0))}`
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: cores.text },
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: cores.text,
                            callback: (value) => formatarMoeda.format(Number(value || 0))
                        },
                        grid: { color: cores.grid }
                    }
                }
            }
        });
        registrarGrafico(canvasTendencia);
    }

    function filtrarCategorias(tipoSelect, categoriaSelect) {
        if (!tipoSelect || !categoriaSelect) return;

        const atualizar = () => {
            const tipoSelecionado = tipoSelect.value;
            const opcoes = categoriaSelect.querySelectorAll("option");

            opcoes.forEach((opcao) => {
                const tipoCategoria = opcao.dataset.tipo;

                if (!opcao.value) {
                    opcao.hidden = false;
                    return;
                }

                opcao.hidden = Boolean(tipoSelecionado && tipoCategoria !== tipoSelecionado);
                if (opcao.hidden && opcao.selected) categoriaSelect.value = "";
            });
        };

        tipoSelect.addEventListener("change", atualizar);
        atualizar();
    }

    function inicializarFiltrosDeCategoria() {
        filtrarCategorias(
            document.getElementById("tipo"),
            document.getElementById("categoria_id")
        );

        document.querySelectorAll(".editar-transacao form").forEach((form) => {
            filtrarCategorias(
                form.querySelector('select[name="tipo"]'),
                form.querySelector('select[name="categoria_id"]')
            );
        });
    }

    function inicializarFiltrosDeTransacoes() {
        const busca = document.querySelector("[data-transaction-search]");
        const tipo = document.querySelector("[data-transaction-type]");
        const linhas = Array.from(document.querySelectorAll("[data-transaction-row]"));
        const vazio = document.querySelector("[data-transaction-empty]");

        if (!linhas.length) return;

        const filtrar = () => {
            const termo = (busca?.value || "").trim().toLowerCase();
            const tipoSelecionado = tipo?.value || "";
            let visiveis = 0;

            linhas.forEach((linha) => {
                const combinaBusca = !termo || (linha.dataset.search || "").includes(termo);
                const combinaTipo = !tipoSelecionado || linha.dataset.type === tipoSelecionado;
                const visivel = combinaBusca && combinaTipo;

                linha.hidden = !visivel;
                if (visivel) visiveis += 1;
            });

            if (vazio) vazio.classList.toggle("is-hidden", visiveis > 0);
        };

        busca?.addEventListener("input", filtrar);
        tipo?.addEventListener("change", filtrar);
        filtrar();
    }

    function inicializarAnimacoes() {
        document.querySelectorAll(".progresso-meta").forEach((barra) => {
            const progresso = parseFloat(barra.dataset.progresso || barra.style.width || 0);
            barra.style.width = "0%";
            setTimeout(() => {
                barra.style.width = `${progresso}%`;
            }, 120);
        });
    }

    function inicializarToasts() {
        document.querySelectorAll(".toast").forEach((toast) => {
            setTimeout(() => {
                toast.classList.add("toast-esconder");
            }, 2800);
        });
    }

    function recriarGraficos() {
        chartInstances.splice(0).forEach((chart) => chart.destroy());
        document.querySelectorAll(".grafico-aviso").forEach((aviso) => aviso.remove());
        document.querySelectorAll("canvas").forEach((canvas) => {
            canvas.style.display = "";
        });
        inicializarGraficoResumo();
        inicializarGraficoTendencia();
    }

    inicializarNavegacaoInterna();
    inicializarGraficoResumo();
    inicializarGraficoTendencia();
    inicializarFiltrosDeCategoria();
    inicializarFiltrosDeTransacoes();
    inicializarAnimacoes();
    inicializarToasts();

    window.addEventListener("grana-theme-change", recriarGraficos);
});
