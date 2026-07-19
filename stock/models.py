from django.contrib.auth.models import User
from django.db import models


class StockCategory(models.Model):
    """
    Categoria de itens para conferência de estoque.
    Ex: Bases, Frutas, Embalagens.
    """

    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordem de exibição")
    active = models.BooleanField(default=True, verbose_name="Ativa")

    class Meta:
        verbose_name = "Categoria de Estoque"
        verbose_name_plural = "Categorias de Estoque"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["active"]),
            models.Index(fields=["sort_order"]),
        ]

    def __str__(self):
        return self.name


class StockItem(models.Model):
    """
    Item individual dentro de uma categoria de estoque.
    Ex: Banana, Nutella, Copo 500 ml.
    """

    category = models.ForeignKey(
        StockCategory,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name="Categoria",
    )
    name = models.CharField(max_length=100, verbose_name="Nome")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordem de exibição")
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Item de Estoque"
        verbose_name_plural = "Itens de Estoque"
        ordering = ["category__sort_order", "sort_order", "name"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["active"]),
            models.Index(fields=["sort_order"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="unique_stock_item_per_category",
            )
        ]

    def __str__(self):
        return f"{self.category.name} / {self.name}"


class StockCheck(models.Model):
    """
    Conferência de estoque de um dia. Apenas uma por data.

    Armazena somente os itens com problema (LOW/OUT); ausência = OK.
    """

    date = models.DateField(unique=True, verbose_name="Data")
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="stock_checks",
        verbose_name="Responsável",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Conferência de Estoque"
        verbose_name_plural = "Conferências de Estoque"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["-date"]),
        ]

    def __str__(self):
        return f"Conferência {self.date.strftime('%d/%m/%Y')}"

    @property
    def item_count(self):
        return self.items.count()


class StockCheckItem(models.Model):
    """
    Item marcado como LOW ou OUT em uma conferência.
    Ausência de registro significa status OK.

    `item_name` é snapshot — preserva o nome caso o item seja renomeado.
    """

    class Status(models.TextChoices):
        LOW = "LOW", "Estoque baixo"
        OUT = "OUT", "Acabou"

    stock_check = models.ForeignKey(
        StockCheck,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Conferência",
    )
    item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name="check_items",
        verbose_name="Item",
    )
    item_name = models.CharField(max_length=100, verbose_name="Item (snapshot)")
    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        verbose_name="Status",
    )
    buy_quantity = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="Quantidade a comprar",
    )

    class Meta:
        verbose_name = "Item da Conferência"
        verbose_name_plural = "Itens da Conferência"
        ordering = ["stock_check", "item_name"]
        indexes = [
            models.Index(fields=["stock_check"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["stock_check", "item"],
                name="unique_item_per_check",
            )
        ]

    def __str__(self):
        return f"{self.item_name} — {self.get_status_display()}"
