from django.contrib import admin
from orders.models import ProductCategory, Size, Product, ProductVariant, Addon


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'sort_order', 'active', 'product_count')
    list_filter = ('kind', 'active')
    search_fields = ('name',)
    ordering = ('sort_order', 'name')

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'kind', 'active')
        }),
        ('Exibição', {
            'fields': ('sort_order',)
        }),
    )

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Produtos'


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'volume_ml', 'sort_order', 'active')
    list_filter = ('active',)
    search_fields = ('name',)
    ordering = ('sort_order', 'volume_ml')

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'volume_ml', 'active')
        }),
        ('Exibição', {
            'fields': ('sort_order',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'product_type', 'sort_order', 'active', 'variant_count')
    list_filter = ('product_type', 'category', 'active')
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')
    autocomplete_fields = ['category']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'category', 'product_type', 'active')
        }),
        ('Detalhes', {
            'fields': ('description',)
        }),
        ('Exibição', {
            'fields': ('sort_order',)
        }),
    )

    def variant_count(self, obj):
        return obj.variants.count()
    variant_count.short_description = 'Variações'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('size', 'price', 'included_addons_limit', 'active')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'product', 'size', 'display_price', 'included_addons_limit', 'active')
    list_filter = ('active', 'product__category')
    search_fields = ('product__name',)
    ordering = ('product__sort_order', 'product__name', 'size__sort_order')
    autocomplete_fields = ['product', 'size']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('product', 'size', 'price', 'active')
        }),
        ('Adicionais (Monte seu Açaí)', {
            'fields': ('included_addons_limit',),
            'classes': ('collapse',),
            'description': 'Preencha apenas para produtos do tipo Monte seu Açaí.'
        }),
    )

    def display_price(self, obj):
        return f"R$ {obj.price:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    display_price.short_description = 'Preço'


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_price', 'is_free_option', 'sort_order', 'active')
    list_filter = ('is_free_option', 'active')
    search_fields = ('name',)
    ordering = ('sort_order', 'name')

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'price', 'active')
        }),
        ('Monte seu Açaí', {
            'fields': ('is_free_option',),
            'description': 'Marque se este adicional pode ser incluído gratuitamente no Monte seu Açaí.'
        }),
        ('Exibição', {
            'fields': ('sort_order',)
        }),
    )

    def display_price(self, obj):
        return f"R$ {obj.price:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    display_price.short_description = 'Preço'
