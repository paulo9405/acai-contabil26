"""
Testes do management command load_catalog — Fase 2.
"""
import pytest
from decimal import Decimal
from io import StringIO
from django.core.management import call_command

from orders.models import ProductCategory, Size, Product, ProductVariant, Addon


@pytest.mark.django_db
class TestLoadCatalog:

    def _run(self, **kwargs):
        out = StringIO()
        call_command('load_catalog', stdout=out, **kwargs)
        return out.getvalue()

    def test_cria_tamanhos(self):
        self._run()
        assert Size.objects.count() == 6

    def test_cria_categorias(self):
        self._run()
        assert ProductCategory.objects.count() == 5

    def test_cria_adicionais(self):
        self._run()
        assert Addon.objects.count() == 27

    def test_cria_produtos(self):
        self._run()
        assert Product.objects.count() == 24

    def test_cria_variacoes(self):
        self._run()
        assert ProductVariant.objects.count() == 88

    def test_idempotente_sem_duplicar(self):
        self._run()
        self._run()
        assert Size.objects.count() == 6
        assert ProductCategory.objects.count() == 5
        assert Addon.objects.count() == 27
        assert Product.objects.count() == 24
        assert ProductVariant.objects.count() == 88

    def test_idempotente_relatorio_sem_criacao(self):
        self._run()
        out = self._run()
        assert 'criados: 0' in out
        assert 'sem alteração: 150' in out

    def test_spot_acai_oreo_500ml(self):
        self._run()
        v = ProductVariant.objects.get(product__name='13 Açaí Oreo', size__name='500 ml')
        assert v.price == Decimal('26.00')

    def test_spot_monte_acai_500ml_limite(self):
        self._run()
        v = ProductVariant.objects.get(product__name='Monte seu Açaí', size__name='500 ml')
        assert v.included_addons_limit == 3

    def test_spot_monte_acai_todos_limites(self):
        self._run()
        limites_esperados = {
            '300 ml': 2, '500 ml': 3, '700 ml': 3,
            '1 litro': 4, '1,5 litro': 5, '2 litros': 6,
        }
        for size_name, limite in limites_esperados.items():
            v = ProductVariant.objects.get(product__name='Monte seu Açaí', size__name=size_name)
            assert v.included_addons_limit == limite, (
                f'Monte seu Açaí {size_name}: esperado {limite}, got {v.included_addons_limit}'
            )

    def test_sorvete_sem_tamanho(self):
        self._run()
        v = ProductVariant.objects.get(product__name='Sorvete Ninho Trufado')
        assert v.size is None
        assert v.price == Decimal('39.00')

    def test_vitamina_500ml(self):
        self._run()
        v = ProductVariant.objects.get(product__name='Vitamina Whey Protein')
        assert v.size.name == '500 ml'
        assert v.price == Decimal('25.00')

    def test_granola_is_free_option(self):
        self._run()
        addon = Addon.objects.get(name='Granola')
        assert addon.is_free_option is True

    def test_nutella_nao_is_free_option(self):
        self._run()
        addon = Addon.objects.get(name='Nutella')
        assert addon.is_free_option is False
        assert addon.price == Decimal('7.50')

    def test_combo_familia_apenas_15l_e_2l(self):
        self._run()
        product = Product.objects.get(name='10 Combo Família')
        sizes = set(product.variants.values_list('size__name', flat=True))
        assert sizes == {'1,5 litro', '2 litros'}

    def test_acai_zero_apenas_ate_1l(self):
        self._run()
        product = Product.objects.get(name='11 Açaí Zero')
        sizes = set(product.variants.values_list('size__name', flat=True))
        assert sizes == {'300 ml', '500 ml', '700 ml', '1 litro'}

    def test_dry_run_nao_salva(self):
        self._run(dry_run=True)
        assert Size.objects.count() == 0
        assert ProductCategory.objects.count() == 0
        assert Addon.objects.count() == 0

    def test_monte_acai_product_type(self):
        self._run()
        product = Product.objects.get(name='Monte seu Açaí')
        assert product.product_type == Product.ProductType.BUILD_YOUR_OWN

    def test_categoria_monte_acai_kind(self):
        self._run()
        cat = ProductCategory.objects.get(name='Monte seu Açaí')
        assert cat.kind == ProductCategory.Kind.BUILD_YOUR_OWN

    def test_categoria_adicionais_kind(self):
        self._run()
        cat = ProductCategory.objects.get(name='Adicionais')
        assert cat.kind == ProductCategory.Kind.ADDON
