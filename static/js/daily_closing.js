/**
 * Fechamento do Dia — Lógica da tabela dinâmica de despesas.
 *
 * Responsabilidades:
 *  - Adicionar / remover linhas de despesa sem recarregar a página
 *  - Calcular totais em tempo real (vendas, despesas, resultado)
 *  - Validar linhas incompletas antes do envio
 *  - Remover silenciosamente linhas completamente vazias no envio
 */
(function () {
    'use strict';

    // =========================================================================
    // Referências ao DOM
    // =========================================================================
    const form      = document.getElementById('fechamento-form');
    const tbody     = document.getElementById('despesas-tbody');
    const btnAdd    = document.getElementById('btn-adicionar-despesa');
    const tmpl      = document.getElementById('despesa-row-template');

    const inCash    = document.getElementById('id_cash_sales');
    const inPix     = document.getElementById('id_pix_sales');
    const inCard    = document.getElementById('id_card_sales');
    const inOrders  = document.getElementById('id_order_count');

    const elTotalVendas  = document.getElementById('display-total-vendas');
    const elTicket       = document.getElementById('display-ticket-medio');
    const elTotalDesp    = document.getElementById('display-total-despesas');
    const elResVendas    = document.getElementById('resumo-vendas');
    const elResDespesas  = document.getElementById('resumo-despesas');
    const elResultado    = document.getElementById('resumo-resultado');

    let isSubmitting = false;

    // =========================================================================
    // Utilitários
    // =========================================================================

    /** Lê o valor numérico de um input; retorna 0 se vazio ou inválido. */
    function num(input) {
        if (!input) return 0;
        const v = parseFloat(input.value);
        return isNaN(v) || v < 0 ? 0 : v;
    }

    /** Formata um número como moeda brasileira sem símbolo de padding extra. */
    function fmt(value) {
        return 'R$ ' + value.toFixed(2).replace('.', ',');
    }

    /** Define o texto de um elemento, se ele existir. */
    function setText(el, text) {
        if (el) el.textContent = text;
    }

    // =========================================================================
    // Cálculos e atualização de totais
    // =========================================================================

    function totalSales() {
        return num(inCash) + num(inPix) + num(inCard);
    }

    function totalExpenses() {
        let total = 0;
        tbody.querySelectorAll('.expense-amount-input').forEach(function (inp) {
            total += num(inp);
        });
        return total;
    }

    /**
     * Recalcula todos os totais e atualiza o DOM.
     * Chamada sempre que qualquer campo de vendas ou despesas muda.
     */
    function refresh() {
        const sales    = totalSales();
        const orders   = parseInt((inOrders ? inOrders.value : '0'), 10) || 0;
        const ticket   = orders > 0 ? sales / orders : 0;
        const expenses = totalExpenses();
        const result   = sales - expenses;

        setText(elTotalVendas, fmt(sales));
        setText(elTicket,      fmt(ticket));
        setText(elTotalDesp,   fmt(expenses));
        setText(elResVendas,   fmt(sales));
        setText(elResDespesas, fmt(expenses));

        if (elResultado) {
            elResultado.textContent = fmt(result);
            elResultado.className   =
                'fs-5 fw-bold ' + (result >= 0 ? 'text-primary' : 'text-danger');
        }
    }

    // =========================================================================
    // Gerenciamento de linhas
    // =========================================================================

    /** Retorna todas as linhas de despesa (exclui linha de estado vazio e erros). */
    function expenseRows() {
        return Array.from(tbody.querySelectorAll('tr[data-expense-row]'));
    }

    function showEmptyState() {
        if (tbody.querySelector('#empty-despesas-row')) return;
        const tr  = document.createElement('tr');
        tr.id     = 'empty-despesas-row';
        tr.innerHTML =
            '<td colspan="4" class="text-center text-muted py-4">' +
            '<i class="bi bi-receipt d-block mb-2" style="font-size:1.5rem;opacity:.3"></i>' +
            '<small>Nenhuma despesa lançada. Clique em “+ Adicionar outra despesa” para começar.</small>' +
            '</td>';
        tbody.appendChild(tr);
    }

    function hideEmptyState() {
        const el = tbody.querySelector('#empty-despesas-row');
        if (el) el.remove();
    }

    /** Cria e adiciona uma nova linha de despesa ao tbody. */
    function addRow() {
        hideEmptyState();

        const clone = tmpl.content.cloneNode(true);
        const tr    = clone.querySelector('tr');
        tr.setAttribute('data-expense-row', '1');
        tbody.appendChild(clone);

        // Foca o primeiro campo (select de categoria) da nova linha
        const newTr     = tbody.lastElementChild;
        const firstField = newTr ? newTr.querySelector('select') : null;
        if (firstField) firstField.focus();

        refresh();
    }

    /** Remove uma linha de despesa e, se necessário, exibe o estado vazio. */
    function removeRow(btn) {
        const tr   = btn.closest('tr');
        if (!tr) return;

        // Remove eventual linha de erro logo abaixo
        const next = tr.nextElementSibling;
        if (next && next.classList.contains('row-error')) next.remove();

        tr.remove();

        if (expenseRows().length === 0) showEmptyState();
        refresh();
    }

    // =========================================================================
    // Erros inline
    // =========================================================================

    function clearErrors() {
        tbody.querySelectorAll('.row-error').forEach(function (el) { el.remove(); });
        tbody.querySelectorAll('.is-invalid').forEach(function (el) {
            el.classList.remove('is-invalid');
        });
    }

    /**
     * Insere uma linha de erro imediatamente após a linha com problema.
     * Evita duplicar caso já exista um erro naquela linha.
     */
    function addRowError(tr, message) {
        const next = tr.nextElementSibling;
        if (next && next.classList.contains('row-error')) return;

        const errTr = document.createElement('tr');
        errTr.className = 'row-error';
        errTr.innerHTML =
            '<td colspan="4" class="pb-2 ps-3">' +
            '<small class="text-danger">⚠ ' + message + '</small>' +
            '</td>';
        tr.after(errTr);
    }

    // =========================================================================
    // Validação e envio do formulário
    // =========================================================================

    function handleSubmit(e) {
        if (isSubmitting) {
            e.preventDefault();
            return;
        }

        clearErrors();

        let hasError   = false;
        const toRemove = [];

        expenseRows().forEach(function (tr) {
            const catSel  = tr.querySelector('select[name="expense_category[]"]');
            const amtInp  = tr.querySelector('input[name="expense_amount[]"]');
            const descInp = tr.querySelector('input[name="expense_description[]"]');

            const catVal  = catSel  ? catSel.value.trim()     : '';
            const amtVal  = amtInp  ? num(amtInp)             : 0;
            const descVal = descInp ? descInp.value.trim()    : '';

            // Linha totalmente vazia → remover silenciosamente
            if (!catVal && amtVal === 0 && !descVal) {
                toRemove.push(tr);
                return;
            }

            // Linha parcial: tem categoria mas não tem valor
            if (catVal && amtVal === 0) {
                if (amtInp) amtInp.classList.add('is-invalid');
                addRowError(tr, 'Informe o valor desta despesa.');
                hasError = true;
                return;
            }

            // Linha parcial: tem valor mas não tem categoria
            if (!catVal && amtVal > 0) {
                if (catSel) catSel.classList.add('is-invalid');
                addRowError(tr, 'Selecione a categoria desta despesa.');
                hasError = true;
            }
        });

        // Remove as linhas vazias antes de enviar
        toRemove.forEach(function (tr) { tr.remove(); });

        if (hasError) {
            e.preventDefault();
            const firstInvalid = tbody.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalid.focus();
            }
            return;
        }

        isSubmitting = true;
        const btnSubmit = form ? form.querySelector('button[type="submit"]') : null;
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.textContent = 'Salvando…';
        }
    }

    // =========================================================================
    // Delegação de eventos no tbody (cobre linhas estáticas e dinâmicas)
    // =========================================================================

    tbody.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-remover-despesa');
        if (btn) removeRow(btn);
    });

    tbody.addEventListener('input', function (e) {
        if (!e.target.classList.contains('expense-amount-input')) return;

        // Limpa erro da linha ao corrigir o valor
        const tr = e.target.closest('tr');
        if (tr) {
            const next = tr.nextElementSibling;
            if (next && next.classList.contains('row-error')) next.remove();
            e.target.classList.remove('is-invalid');
        }
        refresh();
    });

    // Limpa erro do select de categoria ao selecionar uma opção
    tbody.addEventListener('change', function (e) {
        const sel = e.target.closest('select[name="expense_category[]"]');
        if (!sel) return;
        sel.classList.remove('is-invalid');
        const tr   = sel.closest('tr');
        const next = tr ? tr.nextElementSibling : null;
        if (next && next.classList.contains('row-error')) next.remove();
    });

    // =========================================================================
    // Inputs de vendas (recalculo em tempo real)
    // =========================================================================

    [inCash, inPix, inCard, inOrders].forEach(function (inp) {
        if (inp) inp.addEventListener('input', refresh);
    });

    // =========================================================================
    // Inicialização
    // =========================================================================

    if (btnAdd) btnAdd.addEventListener('click', addRow);
    if (form)   form.addEventListener('submit', handleSubmit);

    // Garante que o cálculo inicial reflete o estado do servidor
    refresh();

})();
