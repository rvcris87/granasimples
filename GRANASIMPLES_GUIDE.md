# GranaSimples — Guia de Diretrizes Técnicas e Visuais

Este documento define as regras visuais, diretrizes de design de interface (UI/UX) e restrições técnicas do projeto **GranaSimples**. O objetivo é garantir consistência visual, legibilidade de dados financeiros e integridade funcional durante a fase de refinamento.

---

## 📌 1. Restrições Técnicas de Back-End (P0)

> [!IMPORTANT]
> A lógica de negócio e a persistência de dados do GranaSimples estão homologadas e estabilizadas. Quaisquer alterações devem focar exclusivamente na camada de apresentação (HTML, CSS e JavaScript de interface).

* **Sem Reescrita Financeira:** É expressamente proibido alterar a lógica de cálculo de saldos, fluxo de metas, transações, gastos fixos ou rotinas de exportação de dados.
* **Preservação de Queries SQL:** Não altere nenhuma consulta SQL existente no arquivo `utils.py`, `routes/` ou scripts de migração.
* **Segurança e Conformidade:**
  * O fluxo de consentimento da **LGPD** deve permanecer intacto e funcional.
  * A proteção **CSRF** (através de tokens gerados pelo `Flask-WTF`) deve continuar ativa em todos os formulários.
  * As diretivas de cookies de sessão (`HTTPOnly`, `SameSite=Lax`, `Secure`) não devem ser alteradas.

---

## 🎨 2. Identidade Visual e Design System

O GranaSimples adota uma estética **Fintech Clean & Minimalist**, priorizando a clareza analítica em detrimento de ornamentos visuais desnecessários.

```
                  ┌─────────────────────────────┐
                  │   GRANASIMPLES PALETTE      │
                  ├─────────────────────────────┤
                  │  [ ] Emerald: #22c55e       │
                  │  [ ] Orange:  #ef4444       │
                  │  [ ] Petrol:  #0e7490       │
                  │  [ ] Charcoal:#0f172a       │
                  │  [ ] Ice Bg:  #f8fafc       │
                  └─────────────────────────────┘
```

### 🚫 A Regra de Proibição do Roxo (Purple Ban)
* **Proibido:** Tons de violeta, roxo, magenta, índigo ou qualquer variação semelhante.
* **Justificativa:** Evitar o clichê visual de "aplicativo moderno gerado por IA" e focar em cores financeiras tradicionais e de alta legibilidade.

### 🎨 Paleta de Cores e Contraste
O app deve suportar perfeitamente os modos **Claro (Light)** e **Escuro (Dark)** baseado nas variáveis CSS (`:root` e `[data-theme="dark"]`).

| Elemento | Tema Claro (Light) | Tema Escuro (Dark) | Aplicação |
| :--- | :--- | :--- | :--- |
| **Background Principal** | `#f8fafc` (Ice) | `#07111f` (Deep Blue/Navy) | Fundo da tela |
| **Superfície (Cards/Painéis)**| `#ffffff` (Branco) | `#0f1b2d` (Navy Escuro) | Blocos de conteúdo |
| **Acento Positivo** | `#22c55e` (Verde Esmeralda) | `#22c55e` | Entradas, saldos positivos, sucesso |
| **Acento Negativo** | `#ef4444` (Vermelho Coral) | `#ef4444` | Saídas, saldos negativos, exclusão |
| **Acento Inteligência** | `#0e7490` (Petrol/Teal) | `#2563eb` (Azul Técnico) | Gráficos, destaques e metas |
| **Texto Principal** | `#0f172a` (Charcoal) | `#f8fafc` | Leitura principal |
| **Texto Secundário** | `#64748b` (Slate-500) | `#94a3b8` | Legendas, metadados e spans |

### 📐 Geometria e Layout (Anti-SaaS Cliché)
* **Bordas e Cantos:**
  * Cards, tabelas e contêineres técnicos devem usar cantos nítidos de **`2px` a `8px`** (estilo preciso/analítico).
  * Modais, menus flutuantes e botões de ação maiores podem usar cantos arredondados de até **`12px`**.
  * Evitar o uso indiscriminado de cantos excessivamente arredondados (`rounded-2xl` ou `rounded-3xl`) que infantilizam a interface.
* **Layout Asimétrico:**
  * Em vez do layout padrão 50/50 em telas divididas, priorize grids com tensões visuais organizadas (como `1/3` para formulários e `2/3` para visualização de dados).
* **Fórmula do Saldo Disponível:**
  * O principal elemento da "Visão Geral" deve ser o card de **Saldo Disponível**. Ele deve ter destaque visual hierárquico absoluto, diagramado de modo a demonstrar graficamente a equação:
    $$\text{Saldo Disponível} = \text{Saldo Acumulado Histórico} - \text{Total Reservado em Metas}$$

---

## ⚡ 3. UI/UX, Interatividade e Acessibilidade

### 📱 Mobile-First Real (Funcionalidade sobre Estética)
* O layout em dispositivos móveis deve ser **estritamente de coluna única** ou com rolagem lateral bem definida.
* Elementos clicáveis na tela do celular devem possuir área de toque mínima de **`44px` por `44px`** para evitar erros de toque do usuário.
* O menu lateral (sidebar) deve colapsar de forma limpa em um menu hambúrguer ou barra inferior compacta em telas menores que `768px`.

### ⏱️ Animações e Micro-interações
* **Sutileza:** Animações não devem ser longas ou intrusivas. O tempo de transição padrão para hovers e revelações deve ser entre **`150ms` e `250ms`** usando funções `ease` ou `cubic-bezier` de aceleração natural.
* **Otimização de Renderização:**
  * Use apenas propriedades aceleradas por GPU (`transform`, `opacity`).
  * Não use filtros pesados de borrão (`backdrop-filter: blur()`) em cascata ou repetição no modo escuro.
* **Acessibilidade:** Respeitar a diretiva `@media (prefers-reduced-motion: reduce)` removendo transições de movimento para usuários que desativaram animações no sistema operacional.

### 🧩 Componentes Customizados
* **Elementos `<details>`:** Ao usar sanfonas nativas do HTML para edição ou detalhes de categorias, estilize os cabeçalhos ocultando o marcador do navegador (`summary::-webkit-details-marker`) e aplicando um chevron do FontAwesome que rotaciona suavemente em `90deg` ou `180deg` ao expandir.
* **Inputs de Data/Select:** Devem ter estilização consistente que oculte as bordas nativas do sistema operacional, mantendo foco nítido usando a cor de acento de marca e anéis de foco (`box-shadow: var(--ring)`).

---

## 🛠️ 4. Fluxo de Trabalho para Desenvolvimento Visual

Ao realizar implementações visuais nos templates ou folhas de estilo:
1. **Verificação de Regressão:** Após qualquer alteração de CSS em `static/css/style.css`, verifique se o layout do dashboard permaneceu íntegro tanto em telas desktop quanto mobile.
2. **Auditoria de Acessibilidade (Lighthouse/WCAG):** Certifique-se de que os níveis de contraste dos textos em modo escuro/claro continuam atendendo aos critérios mínimos de legibilidade.
3. **Não poluição de arquivos:** Mantenha os novos estilos organizados em `static/css/style.css` ou em arquivos CSS específicos do módulo (ex: `metas.css`, `gastos-fixos.css`). Evite injetar blocos longos de `<style>` no meio das páginas HTML.
