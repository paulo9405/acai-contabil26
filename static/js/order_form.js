/**
 * Lançamento de Pedido — seleção de catálogo, carrinho e envio.
 *
 * Fluxo: Categoria → Produto → Tamanho → (Adicionais) → Qtd → Adicionar → Lançar
 */
(function () {
    'use strict';

    // =========================================================================
    // Catálogo e mapas de busca rápida
    // =========================================================================
    const catalogEl = document.getElementById('catalog-data');
    if (!catalogEl) return;

    const catalog = JSON.parse(catalogEl.textContent);

    const categoryMap = {};
    const productMap  = {};
    const variantMap  = {};
    const addonMap    = {};

    catalog.categories.forEach(function (cat) {
        categoryMap[cat.id] = cat;
        cat.products.forEach(function (prod) {
            productMap[prod.id] = prod;
            prod.variants.forEach(function (v) {
                variantMap[v.id] = {
                    id:                   v.id,
                    display:              v.display,
                    price:                v.price,
                    included_addons_limit: v.included_addons_limit,
                    productId:            prod.id,
                    productName:          prod.name,
                    productType:          prod.product_type,
                };
            });
        });
    });

    catalog.addons.forEach(function (a) {
        addonMap[a.id] = a;
    });

    // =========================================================================
    // Estado do carrinho e seleção atual
    // =========================================================================
    var cart = [];  // [{variantId, productName, variantDisplay, quantity, unitPrice, addons, lineTotal}]

    var selectedCatId     = null;
    var selectedProdId    = null;
    var selectedVariantId = null;

    // =========================================================================
    // Referências ao DOM
    // =========================================================================
    var catButtons      = document.getElementById('cat-buttons');
    var prodSection     = document.getElementById('prod-section');
    var prodButtons     = document.getElementById('prod-buttons');
    var variantSection  = document.getElementById('variant-section');
    var variantButtons  = document.getElementById('variant-buttons');
    var addonSection    = document.getElementById('addon-section');
    var addonLimitInfo  = document.getElementById('addon-limit-info');
    var addonCheckboxes = document.getElementById('addon-checkboxes');
    var itemQtyInput    = document.getElementById('item-quantity');
    var btnAddItem      = document.getElementById('btn-add-item');
    var cartTbody       = document.getElementById('cart-tbody');
    var cartEmptyRow    = document.getElementById('cart-empty');
    var cartCount       = document.getElementById('cart-count');
    var orderTotal      = document.getElementById('order-total');
    var informedInput   = document.getElementById('id_informed_total');
    var divergenceAlert = document.getElementById('divergence-alert');
    var divergenceMsg   = document.getElementById('divergence-msg');
    var formItems       = document.getElementById('form-items');
    var orderForm       = document.getElementById('order-form');
    var btnSubmit       = document.getElementById('btn-submit');

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
    // Renderização de categorias
    // =========================================================================
    function renderCategories() {
        catButtons.innerHTML = '';
        catalog.categories.forEach(function (cat) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-secondary';
            btn.dataset.catId = cat.id;
            btn.textContent = cat.name;
            btn.addEventListener('click', function () { selectCategory(cat.id); });
            catButtons.appendChild(btn);
        });
    }

    function selectCategory(catId) {
        selectedCatId     = catId;
        selectedProdId    = null;
        selectedVariantId = null;

        catButtons.querySelectorAll('button').forEach(function (b) {
            var active = String(b.dataset.catId) === String(catId);
            b.className = 'btn ' + (active ? 'btn-primary' : 'btn-outline-secondary');
        });

        renderProducts(categoryMap[catId].products);
        clearVariants();
        clearAddons();
        updateAddButton();
    }

    // =========================================================================
    // Renderização de produtos
    // =========================================================================
    function renderProducts(products) {
        prodButtons.innerHTML = '';
        toggleSection(prodSection, true);

        products.forEach(function (prod) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-secondary';
            btn.dataset.prodId = prod.id;
            btn.textContent = prod.name;
            btn.addEventListener('click', function () { selectProduct(prod.id); });
            prodButtons.appendChild(btn);
        });

        if (products.length === 1) selectProduct(products[0].id);
    }

    function selectProduct(prodId) {
        selectedProdId    = prodId;
        selectedVariantId = null;

        prodButtons.querySelectorAll('button').forEach(function (b) {
            var active = String(b.dataset.prodId) === String(prodId);
            b.className = 'btn ' + (active ? 'btn-primary' : 'btn-outline-secondary');
        });

        renderVariants(productMap[prodId].variants);
        clearAddons();
        updateAddButton();
    }

    // =========================================================================
    // Renderização de variantes (tamanhos)
    // =========================================================================
    function renderVariants(variants) {
        variantButtons.innerHTML = '';
        toggleSection(variantSection, true);

        variants.forEach(function (v) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-secondary';
            btn.dataset.variantId = v.id;
            btn.innerHTML = '<span class="fw-medium">' + v.display + '</span>' +
                            '<br><small>' + fmt(v.price) + '</small>';
            btn.addEventListener('click', function () { selectVariant(v.id); });
            variantButtons.appendChild(btn);
        });

        if (variants.length === 1) selectVariant(variants[0].id);
    }

    function selectVariant(variantId) {
        selectedVariantId = variantId;

        variantButtons.querySelectorAll('button').forEach(function (b) {
            var active = String(b.dataset.variantId) === String(variantId);
            b.className = 'btn ' + (active ? 'btn-primary' : 'btn-outline-secondary');
        });

        var v = variantMap[variantId];
        if (v.productType === 'BUILD_YOUR_OWN') {
            renderAddons(v.included_addons_limit);
        } else {
            clearAddons();
        }
        updateAddButton();
    }

    function clearVariants() {
        variantButtons.innerHTML = '';
        toggleSection(variantSection, false);
    }

    // =========================================================================
    // Renderização de adicionais
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
        var limit      = parseInt(addonSection.dataset.limit || '0', 10);
        var freeSlots  = limit;

        addonCheckboxes.querySelectorAll('input[type="checkbox"]').forEach(function (inp) {
            var badge         = addonCheckboxes.querySelector('[data-addon-badge="' + inp.dataset.addonId + '"]');
            if (!badge) return;
            var isFreeOption  = inp.dataset.isFreeOption === '1';
            var price         = parsePrice(inp.dataset.addonPrice);

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

        var checkedFree = addonCheckboxes.querySelectorAll(
            'input[data-is-free-option="1"]:checked'
        ).length;
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
    // Botão "Adicionar"
    // =========================================================================
    function updateAddButton() {
        if (btnAddItem) btnAddItem.disabled = !selectedVariantId;
    }

    function addItemToCart() {
        if (!selectedVariantId) return;

        var v   = variantMap[selectedVariantId];
        var qty = Math.max(1, parseInt(itemQtyInput.value, 10) || 1);

        var limit     = parseInt(addonSection.dataset.limit || '0', 10);
        var freeSlots = limit;
        var addonsCost = 0;
        var addons = [];

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

            addons.push({
                id:         addon.id,
                name:       addon.name,
                cost:       cost,
                isIncluded: isIncluded,
            });
        });

        var lineTotal = (parsePrice(v.price) + addonsCost) * qty;

        cart.push({
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
        var rows = cartTbody.querySelectorAll('tr[data-cart-row]');
        rows.forEach(function (r) { r.remove(); });

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

            var addonsHtml = '';
            if (item.addons.length > 0) {
                var parts = item.addons.map(function (a) {
                    return a.isIncluded ? a.name : (a.name + ' (+' + fmt(a.cost) + ')');
                });
                addonsHtml = '<br><small class="text-muted">' + parts.join(', ') + '</small>';
            }

            tr.innerHTML =
                '<td class="ps-3">' +
                    '<strong>' + item.productName + '</strong>' +
                    (item.variantDisplay ? ' — ' + item.variantDisplay : '') +
                    addonsHtml +
                '</td>' +
                '<td class="text-center">' + item.quantity + '</td>' +
                '<td class="text-end pe-2 fw-medium">' + fmt(item.lineTotal) + '</td>' +
                '<td class="text-center pe-2">' +
                    '<button type="button" class="btn btn-outline-danger btn-sm btn-remove-item" ' +
                    'data-remove-idx="' + idx + '" style="width:34px;height:34px;padding:0" title="Remover">' +
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
    // Reset do seletor após adicionar um item
    // =========================================================================
    function resetItemBuilder() {
        selectedCatId     = null;
        selectedProdId    = null;
        selectedVariantId = null;

        catButtons.querySelectorAll('button').forEach(function (b) {
            b.className = 'btn btn-outline-secondary';
        });
        prodButtons.innerHTML = '';
        toggleSection(prodSection, false);
        clearVariants();
        clearAddons();
        if (itemQtyInput) itemQtyInput.value = 1;
        updateAddButton();
    }

    // =========================================================================
    // Envio do formulário — injeta itens do carrinho como campos ocultos
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

        formItems.innerHTML = '';
        cart.forEach(function (item) {
            function hidden(name, val) {
                var inp = document.createElement('input');
                inp.type  = 'hidden';
                inp.name  = name;
                inp.value = val;
                formItems.appendChild(inp);
            }
            hidden('item_variant_id[]', item.variantId);
            hidden('item_quantity[]',   item.quantity);
            hidden('item_addon_ids[]',  item.addons.map(function (a) { return a.id; }).join(','));
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

    if (btnAddItem)  btnAddItem.addEventListener('click', addItemToCart);
    if (orderForm)   orderForm.addEventListener('submit', handleSubmit);
    if (informedInput) informedInput.addEventListener('input', updateTotal);

    // =========================================================================
    // Inicialização
    // =========================================================================
    renderCategories();
    renderCart();
    updateAddButton();

}());
