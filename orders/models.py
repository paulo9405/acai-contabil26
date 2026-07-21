from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

# Nome da categoria que agrupa itens dados de graça (açaí do cartão fidelidade
# e acréscimos cortesia da Quinta Maluca). Fonte única de verdade — usada no
# seed (load_catalog) e nos relatórios para identificar brindes/cortesias.
GIFT_CATEGORY_NAME = "Brindes"


class ProductCategory(models.Model):
    """
    Categoria do cardápio. O campo `kind` direciona o comportamento na UI de lançamento.
    """

    class Kind(models.TextChoices):
        STANDARD = "STANDARD", "Padrão"
        BUILD_YOUR_OWN = "BUILD_YOUR_OWN", "Monte seu Açaí"
        ADDON = "ADDON", "Adicional"
        OTHER = "OTHER", "Outro"

    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        verbose_name="Tipo",
        help_text="Direciona o comportamento na tela de lançamento",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordem de exibição")
    active = models.BooleanField(default=True, verbose_name="Ativa")

    class Meta:
        verbose_name = "Categoria de Produto"
        verbose_name_plural = "Categorias de Produtos"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["active"]),
            models.Index(fields=["sort_order"]),
        ]

    def __str__(self):
        return self.name


class Size(models.Model):
    """
    Tamanho de produto (ex: 300 ml, 1 litro). Armazena volume em ml para relatórios.
    """

    name = models.CharField(max_length=50, verbose_name="Nome", help_text="Ex: 300 ml, 2 litros")
    volume_ml = models.PositiveIntegerField(
        verbose_name="Volume (ml)",
        help_text="Volume em mililitros — usado em relatórios de litros vendidos",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordem de exibição")
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Tamanho"
        verbose_name_plural = "Tamanhos"
        ordering = ["sort_order", "volume_ml"]
        indexes = [
            models.Index(fields=["active"]),
            models.Index(fields=["sort_order"]),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Produto do cardápio. `product_type` determina como os adicionais se comportam.
    """

    class ProductType(models.TextChoices):
        STANDARD = "STANDARD", "Padrão"
        BUILD_YOUR_OWN = "BUILD_YOUR_OWN", "Monte seu Açaí"
        ADDON = "ADDON", "Adicional"

    category = models.ForeignKey(
        ProductCategory, on_delete=models.PROTECT, related_name="products", verbose_name="Categoria"
    )
    name = models.CharField(max_length=200, verbose_name="Nome")
    description = models.TextField(
        blank=True, verbose_name="Descrição", help_text="Composição do produto"
    )
    product_type = models.CharField(
        max_length=20, choices=ProductType.choices, verbose_name="Tipo de produto"
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordem de exibição")
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["active"]),
            models.Index(fields=["product_type"]),
            models.Index(fields=["sort_order"]),
        ]

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """
    Variação de produto por tamanho e preço.
    Armazena o preço atual e o limite de adicionais incluídos.

    Constraint de unicidade: apenas uma variação por (produto, tamanho).
    Para produtos sem tamanho (size=NULL), a unicidade é validada via clean().
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants", verbose_name="Produto"
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="variants",
        verbose_name="Tamanho",
        help_text="Deixe em branco para produtos sem tamanho",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Preço (R$)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    included_addons_limit = models.PositiveIntegerField(
        default=0,
        verbose_name="Limite de adicionais incluídos",
        help_text="Adicionais gratuitos permitidos (apenas Monte seu Açaí)",
    )
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Variação de Produto"
        verbose_name_plural = "Variações de Produtos"
        ordering = ["product", "size__sort_order"]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["active"]),
        ]
        constraints = [
            # Unicidade (produto, tamanho) quando tamanho não é nulo.
            # A unicidade para size=NULL é garantida via clean().
            models.UniqueConstraint(
                fields=["product", "size"],
                condition=models.Q(size__isnull=False),
                name="unique_product_size_non_null",
            )
        ]

    def clean(self):
        super().clean()
        if self.size is None and self.product_id is not None:
            qs = ProductVariant.objects.filter(product=self.product, size__isnull=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"size": "Já existe uma variação sem tamanho para este produto."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.size:
            return f"{self.product.name} — {self.size.name}"
        return self.product.name


class Addon(models.Model):
    """
    Adicional do cardápio. `is_free_option` indica elegibilidade como adicional gratuito
    no "Monte seu Açaí".
    """

    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Preço (R$)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_free_option = models.BooleanField(
        default=False,
        verbose_name="Elegível como grátis",
        help_text="Pode ser selecionado como adicional incluído no limite do Monte seu Açaí",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordem de exibição")
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Adicional"
        verbose_name_plural = "Adicionais"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["active"]),
            models.Index(fields=["is_free_option"]),
            models.Index(fields=["sort_order"]),
        ]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Pedidos
# ---------------------------------------------------------------------------


class Order(models.Model):
    """
    Pedido lançado pelo funcionário como espelho da comanda física.

    `comanda_number` é apenas referência operacional — sem unicidade (blocos reiniciados).
    O identificador único do sistema é `Order.id`.
    """

    class PaymentMethod(models.TextChoices):
        PIX = "PIX", "Pix"
        CASH = "CASH", "Dinheiro"
        CARD = "CARD", "Cartão"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativo"
        CANCELLED = "CANCELLED", "Cancelado"

    comanda_number = models.CharField(
        max_length=20,
        verbose_name="Número da comanda",
        help_text="Referência do papel físico — não é único",
    )
    order_date = models.DateField(verbose_name="Data")
    order_time = models.TimeField(verbose_name="Horário", help_text="Horário da comanda (HH:MM)")
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices, verbose_name="Forma de pagamento"
    )
    is_split = models.BooleanField(
        default=False,
        verbose_name="Pagamento dividido",
        help_text="True quando o pedido foi pago em mais de uma forma (ver linhas de pagamento).",
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total (calculado)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    informed_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total informado na comanda",
        help_text="Valor escrito na comanda física (opcional)",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE, verbose_name="Status"
    )
    notes = models.TextField(blank=True, verbose_name="Observações")
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="orders", verbose_name="Lançado por"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Cancelado em")
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_orders",
        verbose_name="Cancelado por",
    )
    cancel_reason = models.TextField(blank=True, verbose_name="Motivo do cancelamento")
    idempotency_key = models.UUIDField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="Chave de idempotência",
    )

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-order_date", "order_time"]
        indexes = [
            models.Index(fields=["order_date"]),
            models.Index(fields=["order_date", "payment_method"]),
            models.Index(fields=["order_date", "order_time"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["order_date", "comanda_number"]),
        ]

    @property
    def payment_display(self):
        """Rótulo de pagamento para exibição: 'Misto' quando dividido."""
        if self.is_split:
            return "Misto"
        return self.get_payment_method_display()

    @property
    def has_total_divergence(self):
        """Retorna True se o total informado difere do total calculado."""
        if self.informed_total is None:
            return False
        return self.informed_total != self.total

    def __str__(self):
        date_str = self.order_date.strftime("%d/%m/%Y")
        return f"Pedido #{self.pk} — Comanda {self.comanda_number} ({date_str})"


class OrderItem(models.Model):
    """
    Item de um pedido. Pode ser de catálogo (CATALOG) ou avulso (MANUAL).

    CATALOG: product e variant obrigatórios; preço e snapshots do catálogo; pode ter adicionais.
    MANUAL: product/variant NULL; funcionário informa descrição (product_name),
            unit_price e quantity; sem adicionais, line_total = unit_price × quantity.
    """

    class ItemType(models.TextChoices):
        CATALOG = "CATALOG", "Catálogo"
        MANUAL = "MANUAL", "Avulso"

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Pedido"
    )
    item_type = models.CharField(
        max_length=10,
        choices=ItemType.choices,
        default=ItemType.CATALOG,
        verbose_name="Tipo de item",
        help_text="CATALOG: produto do catálogo; MANUAL: item avulso sem catálogo",
    )
    product = models.ForeignKey(
        "Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Produto",
    )
    variant = models.ForeignKey(
        "ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Variação",
    )
    quantity = models.PositiveIntegerField(verbose_name="Quantidade")
    product_name = models.CharField(max_length=200, verbose_name="Produto (snapshot)")
    variant_name = models.CharField(max_length=100, blank=True, verbose_name="Variação (snapshot)")
    size_name = models.CharField(max_length=50, blank=True, verbose_name="Tamanho (snapshot)")
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Preço unitário (snapshot)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    addons_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total de adicionais pagos",
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total do item",
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["item_type"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.item_type == self.ItemType.CATALOG:
            if self.product_id is None:
                errors["product"] = "Produto é obrigatório para item de catálogo."
            if self.variant_id is None:
                errors["variant"] = "Variação é obrigatória para item de catálogo."
        elif self.item_type == self.ItemType.MANUAL:
            if self.product_id is not None:
                errors["product"] = "Item avulso não deve referenciar produto do catálogo."
            if self.variant_id is not None:
                errors["variant"] = "Item avulso não deve referenciar variação do catálogo."
            if not self.product_name or not self.product_name.strip():
                errors["product_name"] = "Descrição é obrigatória para item avulso."
            if self.unit_price is None or self.unit_price <= Decimal("0.00"):
                errors["unit_price"] = "Valor unitário deve ser maior que zero para item avulso."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.product_name} × {self.quantity} — R$ {self.line_total}"


class OrderItemAddon(models.Model):
    """
    Adicional de um item de pedido. Snapshots do preço e status de inclusão.
    `quantity` é sempre 1 na v1 (campo mantido para evolução futura).
    """

    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="addons", verbose_name="Item do pedido"
    )
    addon = models.ForeignKey(
        "Addon",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_item_addons",
        verbose_name="Adicional",
    )
    name = models.CharField(max_length=100, verbose_name="Adicional (snapshot)")
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Preço unitário (snapshot)",
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    is_included = models.BooleanField(
        verbose_name="Incluído no limite",
        help_text="True = dentro do limite gratuito; False = adicional pago",
    )
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total",
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        verbose_name = "Adicional do Item"
        verbose_name_plural = "Adicionais do Item"
        indexes = [
            models.Index(fields=["addon"]),
        ]

    def __str__(self):
        status = "grátis" if self.is_included else f"R$ {self.unit_price}"
        return f"{self.name} ({status})"


class OrderPayment(models.Model):
    """
    Linha de pagamento de um pedido: uma forma de pagamento e o valor pago nela.

    Fonte única de verdade para os relatórios por forma de pagamento. Um pedido pago
    de forma simples tem exatamente uma linha (amount == total); um pedido dividido
    tem duas ou mais, cuja soma dos `amount` é igual ao `total` do pedido.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payments", verbose_name="Pedido"
    )
    method = models.CharField(
        max_length=10,
        choices=Order.PaymentMethod.choices,
        verbose_name="Forma de pagamento",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor",
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        verbose_name = "Pagamento do Pedido"
        verbose_name_plural = "Pagamentos do Pedido"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["method"]),
        ]

    def __str__(self):
        return f"{self.get_method_display()} — R$ {self.amount}"
