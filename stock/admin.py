from django.contrib import admin

from stock.models import StockCategory, StockCheck, StockCheckItem, StockItem


@admin.register(StockCategory)
class StockCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "active", "item_count")
    list_filter = ("active",)
    search_fields = ("name",)
    ordering = ("sort_order", "name")

    fieldsets = (
        ("Informações", {"fields": ("name", "active")}),
        ("Exibição", {"fields": ("sort_order",)}),
    )

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = "Itens"


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "sort_order", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)
    ordering = ("category__sort_order", "sort_order", "name")
    autocomplete_fields = ["category"]

    fieldsets = (
        ("Informações", {"fields": ("name", "category", "active")}),
        ("Exibição", {"fields": ("sort_order",)}),
    )


class StockCheckItemInline(admin.TabularInline):
    model = StockCheckItem
    extra = 0
    fields = ("item", "item_name", "status")
    readonly_fields = ("item_name",)
    autocomplete_fields = ["item"]


@admin.register(StockCheck)
class StockCheckAdmin(admin.ModelAdmin):
    list_display = ("date", "created_by", "item_count", "created_at", "updated_at")
    list_filter = ("created_by",)
    ordering = ("-date",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [StockCheckItemInline]

    fieldsets = (
        ("Conferência", {"fields": ("date", "created_by")}),
        ("Auditoria", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def item_count(self, obj):
        return obj.item_count

    item_count.short_description = "Itens marcados"
