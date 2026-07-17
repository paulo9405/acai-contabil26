/**
 * Lançamento de Pedido — fluxo por etapas progressivas.
 *
 * Catálogo: Categoria → Produto → Tamanho → (Adicionais) → Qtd → Adicionar → Lançar
 * Avulso:   "Item avulso" → Descrição + Valor + Qtd → Adicionar → Lançar
 */
(function () {
    'use strict';

    // =========================================================================
    // Catálogo e mapas de busca rápida
    // =========================================================================
    var catalogEl = document.getElementById('catalog-data');
    if (!catalogEl) return;

    var catalog = JSON.parse(catalogEl.textContent);

    var categoryMap = {};
    var productMap  = {};
    var variantMap  = {};
    var addonMap    = {};

    catalog.categories.forEach(function (cat) {
        categoryMap[cat.id] = cat;
        cat.products.forEach(function (prod) {
            productMap[prod.id] = prod;
            prod.variants.forEach(function (v) {
                variantMap[v.id] = {
                    id:                    v.id,
                    display:               v.display,
                    price:                 v.price,
                    included_addons_limit: v.included_addons_limit,
                    productId:             prod.id,
                    productName:           prod.name,
                    productType:           prod.product_type,
                };
            });
        });
    });

    catalog.addons.forEach(function (a) {
        addonMap[a.id] = a;
    });

    // =========================================================================
    // Ordem fixa das categorias exibidas (conforme cardápio)
    // =========================================================================
    var CATEGORY_ORDER = ['Açaís Prontos', 'Monte seu Açaí', 'Sorvetes', 'Vitaminas'];

    function getSortedCategories() {
        return CATEGORY_ORDER
            .map(function (name) {
                return catalog.categories.find(function (c) { return c.name === name; });
            })
            .filter(Boolean);
    }

    // =========================================================================
    // Estado do carrinho e seleção atual
    // =========================================================================
    var cart = [];

    var selectedCatId     = null;
    var selectedProdId    = null;
    var selectedVariantId = null;
    var currentMode       = null; // null = catálogo | 'MANUAL' = item avulso

    // =========================================================================
    // Referências ao DOM
    // =========================================================================
    var catStep          = document.getElementById('cat-step');
    var catButtons       = document.getElementById('cat-buttons');
    var prodSection      = document.getElementById('prod-section');
    var prodButtons      = document.getElementById('prod-buttons');
    var variantSection   = document.getElementById('variant-section');
    var variantButtons   = document.getElementById('variant-buttons');
    var addonSection     = document.getElementById('addon-section');
    var addonLimitInfo   = document.getElementById('addon-limit-info');
    var addonCheckboxes  = document.getElementById('addon-checkboxes');
    var confirmSection   = document.getElementById('confirm-section');
    var itemQtyInput     = document.getElementById('item-quantity');
    var btnQtyDec        = document.getElementById('btn-qty-dec');
    var btnQtyInc        = document.getElementById('btn-qty-inc');
    var btnAddItem       = document.getElementById('btn-add-item');
    var cartTbody        = document.getElementById('cart-tbody');
    var cartEmptyRow     = document.getElementById('cart-empty');
    var cartCount        = document.getElementById('cart-count');
    var orderTotal       = document.getElementById('order-total');
    var informedInput    = document.getElementById('id_informed_total');
    var divergenceAlert  = document.getElementById('divergence-alert');
    var divergenceMsg    = document.getElementById('divergence-msg');
    var formItems        = document.getElementById('form-items');
    var orderForm        = document.getElementById('order-form');
    var btnSubmit        = document.getElementById('btn-submit');
    var btnBackStep      = document.getElementById('btn-back-step');
    var stepTitle        = document.getElementById('step-title');

    var cartStateInput   = document.getElementById('cart-state');
    var isSubmitting     = false;

    // Elementos do fluxo avulso
    var manualSection    = document.getElementById('manual-section');
    var manualDescInput  = document.getElementById('manual-desc');
    var manualPriceInput = document.getElementById('manual-price');
    var manualQtyInput   = document.getElementById('manual-quantity');
    var btnManualQtyDec  = document.getElementById('btn-manual-qty-dec');
    var btnManualQtyInc  = document.getElementById('btn-manual-qty-inc');
    var btnAddManual     = document.getElementById('btn-add-manual');
    var btnManualItem    = document.getElementById('btn-manual-item');

    // =========================================================================
    // Utilitários
    // =========================================================================
    function fmt(value) {
        return 'R$ ' + parseFloat(value).toFixed(2).replace('.', ',');
    }

    function parsePrice(str) {
        return parseFloat(str) || 0;
    }

    function toggleSection(el, visible) {
        if (el) el.classList.toggle('d-none', !visible);
    }

    // =========================================================================
    // Gestão de etapas
    // =========================================================================
    var stepHistory = [];

    function showOnlyStep(visibleEl) {
        [catStep, prodSection, variantSection, manualSection].forEach(function (el) {
            toggleSection(el, el === visibleEl);
        });
    }

    function goBack() {
        if (stepHistory.length === 0) return;
        var entry = stepHistory.pop();
        entry.fn();
    }

    function setStepTitle(title, showBack) {
        if (stepTitle) stepTitle.textContent = title;
        toggleSection(btnBackStep, showBack);
    }

    // =========================================================================
    // ETAPA 1: Renderização de categorias
    // =========================================================================
    function renderCategories() {
        catButtons.innerHTML = '';
        getSortedCategories().forEach(function (cat) {
            var col = document.createElement('div');
            col.className = 'col';

            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-primary w-100 fw-medium';
            btn.dataset.catId = cat.id;
            btn.textContent = cat.name;
            btn.addEventListener('click', function () { selectCategory(cat.id); });

            col.appendChild(btn);
            catButtons.appendChild(col);
        });
    }

    function selectCategory(catId) {
        selectedCatId     = catId;
        selectedProdId    = null;
        selectedVariantId = null;

        var cat = categoryMap[catId];

        stepHistory.push({
            fn: function () {
                selectedCatId     = null;
                selectedProdId    = null;
                selectedVariantId = null;
                showOnlyStep(catStep);
                variantButtons.innerHTML = '';
                clearAddons();
                toggleSection(confirmSection, false);
                setStepTitle('Adicionar Item', false);
                updateAddButton();
            }
        });

        showOnlyStep(prodSection);
        clearAddons();
        toggleSection(confirmSection, false);
        setStepTitle(cat.name, true);
        updateAddButton();

        renderProducts(cat.products); // pode auto-avançar para variantes se houver 1 produto
    }

    // =========================================================================
    // ETAPA 2: Renderização de produtos
    // =========================================================================
    function renderProducts(products) {
        prodButtons.innerHTML = '';

        products.forEach(function (prod) {
            var col = document.createElement('div');
            col.className = 'col';

            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-secondary w-100';
            btn.dataset.prodId = prod.id;
            btn.textContent = prod.name;
            btn.addEventListener('click', function () { selectProduct(prod.id); });

            col.appendChild(btn);
            prodButtons.appendChild(col);
        });

        if (products.length === 1) selectProduct(products[0].id);
    }

    function selectProduct(prodId) {
        selectedProdId    = prodId;
        selectedVariantId = null;

        var prod = productMap[prodId];
        var cat  = categoryMap[selectedCatId];

        stepHistory.push({
            fn: function () {
                selectedProdId    = null;
                selectedVariantId = null;
                showOnlyStep(prodSection);
                variantButtons.innerHTML = '';
                clearAddons();
                toggleSection(confirmSection, false);
                setStepTitle(cat ? cat.name : 'Produto', true);
                updateAddButton();
            }
        });

        showOnlyStep(variantSection);
        clearAddons();
        toggleSection(confirmSection, false);
        setStepTitle(prod.name, true);
        updateAddButton();

        renderVariants(prod.variants); // pode auto-avançar se houver 1 variante
    }

    // =========================================================================
    // ETAPA 3: Renderização de variantes (tamanhos)
    // =========================================================================
    function renderVariants(variants) {
        variantButtons.innerHTML = '';

        variants.forEach(function (v) {
            var col = document.createElement('div');
            col.className = 'col';

            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-secondary w-100';
            btn.dataset.variantId = v.id;
            btn.innerHTML =
                '<span class="size-label">' + v.display + '</span>' +
                '<span class="price-tag">' + fmt(v.price) + '</span>';
            btn.addEventListener('click', function () { selectVariant(v.id); });

            col.appendChild(btn);
            variantButtons.appendChild(col);
        });

        if (variants.length === 1) selectVariant(variants[0].id);
    }

    function selectVariant(variantId) {
        selectedVariantId = variantId;

        variantButtons.querySelectorAll('button').forEach(function (b) {
            var isActive = String(b.dataset.variantId) === String(variantId);
            b.className = 'btn w-100 ' + (isActive ? 'btn-primary' : 'btn-outline-secondary');
        });

        var v = variantMap[variantId];
        if (v.productType === 'BUILD_YOUR_OWN') {
            renderAddons(v.included_addons_limit);
        } else {
            clearAddons();
        }
        toggleSection(confirmSection, true);
        updateAddButton();
    }

    // =========================================================================
    // ETAPA 4: Renderização de adicionais (apenas BUILD_YOUR_OWN)
    // =========================================================================
    function renderAddons(limit) {
        addonCheckboxes.innerHTML = '';
        toggleSection(addonSection, true);

        catalog.addons.forEach(function (addon) {
            var col = document.createElement('div');
            col.className = 'col';

            var label = document.createElement('label');
            label.className = 'form-check d-flex align-items-start gap-2 p-2 border rounded h-100';
            label.style.cursor = 'pointer';

            var input = document.createElement('input');
            input.type = 'checkbox';
            input.className = 'form-check-input flex-shrink-0 mt-1';
            input.dataset.addonId      = addon.id;
            input.dataset.addonPrice   = addon.price;
            input.dataset.isFreeOption = addon.is_free_option ? '1' : '0';
            input.addEventListener('change', refreshAddonBadges);

            var textDiv = document.createElement('div');
            textDiv.className = 'lh-sm';

            var nameSpan = document.createElement('span');
            nameSpan.className = 'form-check-label d-block';
            nameSpan.textContent = addon.name;

            var badge = document.createElement('span');
            badge.className = 'badge bg-secondary mt-1';
            badge.dataset.addonBadge = addon.id;
            badge.textContent = addon.is_free_option ? 'Grátis' : fmt(addon.price);

            textDiv.appendChild(nameSpan);
            textDiv.appendChild(badge);
            label.appendChild(input);
            label.appendChild(textDiv);
            col.appendChild(label);
            addonCheckboxes.appendChild(col);
        });

        addonSection.dataset.limit = limit;
        refreshAddonBadges();
        updateAddonLimitInfo(limit);
    }

    function refreshAddonBadges() {
        var limit     = parseInt(addonSection.dataset.limit || '0', 10);
        var freeSlots = limit;

        addonCheckboxes.querySelectorAll('input[type="checkbox"]').forEach(function (inp) {
            var badge        = addonCheckboxes.querySelector('[data-addon-badge="' + inp.dataset.addonId + '"]');
            if (!badge) return;
            var isFreeOption = inp.dataset.isFreeOption === '1';
            var price        = parsePrice(inp.dataset.addonPrice);

            if (inp.checked && isFreeOption && freeSlots > 0) {
                badge.textContent = 'Grátis';
                badge.className   = 'badge bg-success mt-1';
                freeSlots--;
            } else if (inp.checked) {
                badge.textContent = fmt(price);
                badge.className   = 'badge bg-warning text-dark mt-1';
            } else {
                badge.textContent = (isFreeOption && freeSlots > 0) ? 'Grátis' : fmt(price);
                badge.className   = 'badge bg-secondary mt-1';
            }
        });

        var checkedFree = addonCheckboxes.querySelectorAll('input[data-is-free-option="1"]:checked').length;
        var used        = Math.min(checkedFree, limit);
        updateAddonLimitInfo(limit - used);
    }

    function updateAddonLimitInfo(remaining) {
        var limit = parseInt(addonSection.dataset.limit || '0', 10);
        if (addonLimitInfo) {
            addonLimitInfo.textContent = remaining + ' de ' + limit + ' grátis disponível(is)';
            addonLimitInfo.className   = 'badge ms-1 ' + (remaining > 0 ? 'bg-success' : 'bg-secondary');
        }
    }

    function clearAddons() {
        addonCheckboxes.innerHTML = '';
        toggleSection(addonSection, false);
    }

    // =========================================================================
    // Fluxo avulso (MANUAL)
    // =========================================================================
    function selectManualMode() {
        currentMode = 'MANUAL';

        stepHistory.push({
            fn: function () {
                currentMode = null;
                showOnlyStep(catStep);
                clearAddons();
                toggleSection(confirmSection, false);
                setStepTitle('Adicionar Item', false);
                updateManualAddButton();
            }
        });

        showOnlyStep(manualSection);
        toggleSection(confirmSection, false);
        setStepTitle('Item Avulso', true);
        updateManualAddButton();
        if (manualDescInput) manualDescInput.focus();
    }

    function updateManualAddButton() {
        if (!btnAddManual) return;
        var desc  = manualDescInput  ? manualDescInput.value.trim()          : '';
        var price = manualPriceInput ? parseFloat(manualPriceInput.value) || 0 : 0;
        btnAddManual.disabled = !(desc.length > 0 && price > 0);
    }

    function addManualItemToCart() {
        var desc  = manualDescInput  ? manualDescInput.value.trim()          : '';
        var price = manualPriceInput ? parseFloat(manualPriceInput.value) || 0 : 0;
        var qty   = Math.max(1, parseInt(manualQtyInput ? manualQtyInput.value : '1', 10) || 1);

        if (!desc || price <= 0) return;

        cart.push({
            itemType:    'MANUAL',
            description: desc,
            unitPrice:   price,
            quantity:    qty,
            addons:      [],
            lineTotal:   price * qty,
        });

        renderCart();
        resetItemBuilder();
    }

    // =========================================================================
    // Botão "Adicionar ao pedido" (catálogo)
    // =========================================================================
    function updateAddButton() {
        if (btnAddItem) btnAddItem.disabled = !selectedVariantId;
    }

    function addItemToCart() {
        if (!selectedVariantId) return;

        var v   = variantMap[selectedVariantId];
        var qty = Math.max(1, parseInt(itemQtyInput.value, 10) || 1);

        var limit      = parseInt(addonSection.dataset.limit || '0', 10);
        var freeSlots  = limit;
        var addonsCost = 0;
        var addons     = [];

        addonCheckboxes.querySelectorAll('input[type="checkbox"]:checked').forEach(function (inp) {
            var addon        = addonMap[inp.dataset.addonId];
            var isFreeOption = inp.dataset.isFreeOption === '1';
            var cost         = 0;
            var isIncluded   = false;

            if (isFreeOption && freeSlots > 0) {
                isIncluded = true;
                freeSlots--;
            } else {
                cost = parsePrice(inp.dataset.addonPrice);
                addonsCost += cost;
            }

            addons.push({ id: addon.id, name: addon.name, cost: cost, isIncluded: isIncluded });
        });

        var lineTotal = (parsePrice(v.price) + addonsCost) * qty;

        cart.push({
            itemType:       'CATALOG',
            variantId:      v.id,
            productName:    v.productName,
            variantDisplay: v.display,
            quantity:       qty,
            unitPrice:      parsePrice(v.price),
            addons:         addons,
            lineTotal:      lineTotal,
        });

        renderCart();
        resetItemBuilder();
    }

    // =========================================================================
    // Carrinho
    // =========================================================================
    function renderCart() {
        cartTbody.querySelectorAll('tr[data-cart-row]').forEach(function (r) { r.remove(); });

        if (cart.length === 0) {
            toggleSection(cartEmptyRow, true);
            btnSubmit.disabled = true;
            updateTotal();
            return;
        }

        toggleSection(cartEmptyRow, false);
        btnSubmit.disabled = false;

        cart.forEach(function (item, idx) {
            var tr = document.createElement('tr');
            tr.dataset.cartRow = idx;

            var nameCell;
            if (item.itemType === 'MANUAL') {
                nameCell =
                    '<strong>' + item.description + '</strong>' +
                    ' <span class="badge bg-secondary ms-1" style="font-size:.65rem;vertical-align:middle">Avulso</span>';
            } else {
                var addonsHtml = '';
                if (item.addons && item.addons.length > 0) {
                    var parts = item.addons.map(function (a) {
                        return a.isIncluded ? a.name : (a.name + ' (+' + fmt(a.cost) + ')');
                    });
                    addonsHtml = '<br><small class="text-muted">' + parts.join(', ') + '</small>';
                }
                nameCell =
                    '<strong>' + item.productName + '</strong>' +
                    (item.variantDisplay ? ' — ' + item.variantDisplay : '') +
                    addonsHtml;
            }

            tr.innerHTML =
                '<td class="ps-3">' + nameCell + '</td>' +
                '<td class="text-center">' + item.quantity + '</td>' +
                '<td class="text-end pe-2 fw-medium">' + fmt(item.lineTotal) + '</td>' +
                '<td class="text-center pe-2">' +
                    '<button type="button" class="btn btn-outline-danger btn-sm btn-remove-item" ' +
                    'data-remove-idx="' + idx + '" style="width:30px;height:30px;min-height:unset;padding:0" title="Remover">' +
                    '&times;</button>' +
                '</td>';

            cartTbody.insertBefore(tr, cartEmptyRow);
        });

        if (cartCount) cartCount.textContent = cart.length;
        updateTotal();
    }

    function updateTotal() {
        var total = cart.reduce(function (sum, item) { return sum + item.lineTotal; }, 0);
        if (orderTotal) orderTotal.textContent = fmt(total);
        if (cartCount)  cartCount.textContent  = cart.length;

        if (informedInput && informedInput.value.trim()) {
            var informed = parseFloat(informedInput.value);
            if (!isNaN(informed) && Math.abs(informed - total) > 0.005) {
                divergenceMsg.textContent =
                    'O valor informado na comanda (' + fmt(informed) +
                    ') é diferente do total calculado (' + fmt(total) + ').';
                toggleSection(divergenceAlert, true);
            } else {
                toggleSection(divergenceAlert, false);
            }
        } else {
            toggleSection(divergenceAlert, false);
        }
    }

    // =========================================================================
    // Reset do builder após adicionar item
    // =========================================================================
    function resetItemBuilder() {
        selectedCatId     = null;
        selectedProdId    = null;
        selectedVariantId = null;
        currentMode       = null;
        stepHistory.length = 0;

        showOnlyStep(catStep);
        prodButtons.innerHTML    = '';
        variantButtons.innerHTML = '';
        clearAddons();
        toggleSection(confirmSection, false);
        if (itemQtyInput)     itemQtyInput.value     = 1;
        if (manualDescInput)  manualDescInput.value  = '';
        if (manualPriceInput) manualPriceInput.value = '';
        if (manualQtyInput)   manualQtyInput.value   = 1;
        updateAddButton();
        updateManualAddButton();
        setStepTitle('Adicionar Item', false);
    }

    // =========================================================================
    // Envio do formulário — injeta itens como campos ocultos
    // =========================================================================
    function handleSubmit(e) {
        if (cart.length === 0) {
            e.preventDefault();
            var alertEl = document.createElement('div');
            alertEl.className = 'alert alert-danger';
            alertEl.textContent = 'Adicione pelo menos um item ao pedido.';
            orderForm.prepend(alertEl);
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        if (isSubmitting) {
            e.preventDefault();
            return;
        }
        isSubmitting = true;
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.textContent = 'Lançando…';
        }

        // Persiste o carrinho para restauração se houver erro de validação server-side
        if (cartStateInput) {
            cartStateInput.value = JSON.stringify(cart);
        }

        formItems.innerHTML = '';
        cart.forEach(function (item) {
            function hidden(name, val) {
                var inp = document.createElement('input');
                inp.type  = 'hidden';
                inp.name  = name;
                inp.value = val;
                formItems.appendChild(inp);
            }

            var itype = item.itemType || 'CATALOG';
            hidden('item_type[]',     itype);
            hidden('item_quantity[]', item.quantity);

            if (itype === 'MANUAL') {
                hidden('item_variant_id[]',         '');
                hidden('item_addon_ids[]',          '');
                hidden('item_manual_description[]', item.description);
                hidden('item_manual_unit_price[]',  item.unitPrice.toFixed(2));
            } else {
                hidden('item_variant_id[]',         item.variantId);
                hidden('item_addon_ids[]',          item.addons.map(function (a) { return a.id; }).join(','));
                hidden('item_manual_description[]', '');
                hidden('item_manual_unit_price[]',  '');
            }
        });
    }

    // =========================================================================
    // Eventos
    // =========================================================================
    cartTbody.addEventListener('click', function (e) {
        var btn = e.target.closest('.btn-remove-item');
        if (!btn) return;
        var idx = parseInt(btn.dataset.removeIdx, 10);
        cart.splice(idx, 1);
        renderCart();
    });

    if (btnAddItem)    btnAddItem.addEventListener('click', addItemToCart);
    if (btnAddManual)  btnAddManual.addEventListener('click', addManualItemToCart);
    if (btnManualItem) btnManualItem.addEventListener('click', selectManualMode);
    if (orderForm)     orderForm.addEventListener('submit', handleSubmit);
    if (informedInput) informedInput.addEventListener('input', updateTotal);
    if (btnBackStep)   btnBackStep.addEventListener('click', goBack);

    if (btnQtyDec) {
        btnQtyDec.addEventListener('click', function () {
            var v = parseInt(itemQtyInput.value, 10) || 1;
            if (v > 1) itemQtyInput.value = v - 1;
        });
    }
    if (btnQtyInc) {
        btnQtyInc.addEventListener('click', function () {
            var v = parseInt(itemQtyInput.value, 10) || 1;
            if (v < 99) itemQtyInput.value = v + 1;
        });
    }

    if (btnManualQtyDec) {
        btnManualQtyDec.addEventListener('click', function () {
            var v = parseInt(manualQtyInput.value, 10) || 1;
            if (v > 1) manualQtyInput.value = v - 1;
        });
    }
    if (btnManualQtyInc) {
        btnManualQtyInc.addEventListener('click', function () {
            var v = parseInt(manualQtyInput.value, 10) || 1;
            if (v < 99) manualQtyInput.value = v + 1;
        });
    }

    if (manualDescInput)  manualDescInput.addEventListener('input', updateManualAddButton);
    if (manualPriceInput) manualPriceInput.addEventListener('input', updateManualAddButton);

    // =========================================================================
    // Inicialização
    // =========================================================================

    // Restaura o carrinho se a página re-renderizou por erro de validação
    if (cartStateInput && cartStateInput.value) {
        try {
            var savedCart = JSON.parse(cartStateInput.value);
            if (Array.isArray(savedCart) && savedCart.length > 0) {
                cart = savedCart;
            }
        } catch (e) {}
    }

    renderCategories();
    renderCart();
    updateAddButton();
    updateManualAddButton();

}());
