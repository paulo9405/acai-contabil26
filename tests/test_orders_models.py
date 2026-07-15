"""
Testes dos models do app orders — Fase 1: Catálogo.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from orders.models import ProductCategory, Size, Product, ProductVariant, Addon
from tests.conftest import (
    ProductCategoryFactory,
    SizeFactory,
    ProductFactory,
    ProductVariantFactory,
    AddonFactory,
)


@pytest.mark.django_db
class TestProductCategory:

    def test_create(self):
        cat = ProductCategoryFactory(name='Açaís Prontos', kind=ProductCategory.Kind.STANDARD)
        assert cat.pk is not None
        assert cat.name == 'Açaís Prontos'
        assert cat.kind == ProductCategory.Kind.STANDARD
        assert cat.active is True

    def test_str(self):
        cat = ProductCategoryFactory(name='Monte seu Açaí')
        assert str(cat) == 'Monte seu Açaí'

    def test_active_default(self):
        cat = ProductCategoryFactory()
        assert cat.active is True

    def test_inactive(self):
        cat = ProductCategoryFactory(active=False)
        assert cat.active is False

    def test_unique_name(self):
        ProductCategoryFactory(name='Sorvetes')
        with pytest.raises(Exception):
            ProductCategoryFactory(name='Sorvetes')

    def test_kind_choices(self):
        for kind in ProductCategory.Kind:
            cat = ProductCategoryFactory(kind=kind)
            assert cat.kind == kind


@pytest.mark.django_db
class TestSize:

    def test_create(self):
        size = SizeFactory(name='500 ml', volume_ml=500, sort_order=1)
        assert size.pk is not None
        assert size.name == '500 ml'
        assert size.volume_ml == 500
        assert size.active is True

    def test_str(self):
        size = SizeFactory(name='1 litro')
        assert str(size) == '1 litro'

    def test_active_default(self):
        size = SizeFactory()
        assert size.active is True

    def test_inactive(self):
        size = SizeFactory(active=False)
        assert size.active is False


@pytest.mark.django_db
class TestProduct:

    def test_create(self):
        cat = ProductCategoryFactory(kind=ProductCategory.Kind.STANDARD)
        product = ProductFactory(
            category=cat,
            name='Açaí Nutella',
            product_type=Product.ProductType.STANDARD
        )
        assert product.pk is not None
        assert product.name == 'Açaí Nutella'
        assert product.category == cat
        assert product.active is True

    def test_str(self):
        product = ProductFactory(name='Açaí Oreo')
        assert str(product) == 'Açaí Oreo'

    def test_active_default(self):
        product = ProductFactory()
        assert product.active is True

    def test_inactive(self):
        product = ProductFactory(active=False)
        assert product.active is False

    def test_product_type_choices(self):
        for ptype in Product.ProductType:
            product = ProductFactory(product_type=ptype)
            assert product.product_type == ptype

    def test_category_protect_on_delete(self):
        from django.db import IntegrityError
        cat = ProductCategoryFactory()
        ProductFactory(category=cat)
        with pytest.raises(Exception):
            cat.delete()


@pytest.mark.django_db
class TestProductVariant:

    def test_create_with_size(self):
        product = ProductFactory()
        size = SizeFactory(name='300 ml', volume_ml=300)
        variant = ProductVariantFactory(product=product, size=size, price=Decimal('18.00'))
        assert variant.pk is not None
        assert variant.price == Decimal('18.00')
        assert variant.size == size
        assert variant.included_addons_limit == 0
        assert variant.active is True

    def test_create_without_size(self):
        product = ProductFactory()
        variant = ProductVariantFactory(product=product, size=None, price=Decimal('25.00'))
        assert variant.pk is not None
        assert variant.size is None

    def test_str_with_size(self):
        product = ProductFactory(name='Açaí Puro')
        size = SizeFactory(name='500 ml')
        variant = ProductVariantFactory(product=product, size=size)
        assert str(variant) == 'Açaí Puro — 500 ml'

    def test_str_without_size(self):
        product = ProductFactory(name='Vitamina Açaí')
        variant = ProductVariantFactory(product=product, size=None)
        assert str(variant) == 'Vitamina Açaí'

    def test_included_addons_limit(self):
        cat = ProductCategoryFactory(kind=ProductCategory.Kind.BUILD_YOUR_OWN)
        product = ProductFactory(category=cat, product_type=Product.ProductType.BUILD_YOUR_OWN)
        size = SizeFactory(name='500 ml', volume_ml=500)
        variant = ProductVariantFactory(product=product, size=size, included_addons_limit=3)
        assert variant.included_addons_limit == 3

    def test_duplicate_product_size_raises(self):
        product = ProductFactory()
        size = SizeFactory()
        ProductVariantFactory(product=product, size=size)
        with pytest.raises(Exception):
            ProductVariantFactory(product=product, size=size)

    def test_duplicate_null_size_raises(self):
        product = ProductFactory()
        ProductVariantFactory(product=product, size=None)
        with pytest.raises(ValidationError):
            ProductVariantFactory(product=product, size=None)

    def test_different_products_can_share_size(self):
        size = SizeFactory()
        product1 = ProductFactory()
        product2 = ProductFactory()
        v1 = ProductVariantFactory(product=product1, size=size)
        v2 = ProductVariantFactory(product=product2, size=size)
        assert v1.pk != v2.pk

    def test_same_product_different_sizes_allowed(self):
        product = ProductFactory()
        size1 = SizeFactory(name='300 ml', volume_ml=300)
        size2 = SizeFactory(name='500 ml', volume_ml=500)
        v1 = ProductVariantFactory(product=product, size=size1)
        v2 = ProductVariantFactory(product=product, size=size2)
        assert v1.pk != v2.pk

    def test_active_default(self):
        variant = ProductVariantFactory()
        assert variant.active is True

    def test_inactive(self):
        variant = ProductVariantFactory(active=False)
        assert variant.active is False


@pytest.mark.django_db
class TestAddon:

    def test_create(self):
        addon = AddonFactory(name='Nutella', price=Decimal('7.50'), is_free_option=False)
        assert addon.pk is not None
        assert addon.name == 'Nutella'
        assert addon.price == Decimal('7.50')
        assert addon.is_free_option is False
        assert addon.active is True

    def test_str(self):
        addon = AddonFactory(name='Granola')
        assert str(addon) == 'Granola'

    def test_free_option(self):
        addon = AddonFactory(is_free_option=True)
        assert addon.is_free_option is True

    def test_active_default(self):
        addon = AddonFactory()
        assert addon.active is True

    def test_inactive(self):
        addon = AddonFactory(active=False)
        assert addon.active is False

    def test_unique_name(self):
        AddonFactory(name='Banana')
        with pytest.raises(Exception):
            AddonFactory(name='Banana')
