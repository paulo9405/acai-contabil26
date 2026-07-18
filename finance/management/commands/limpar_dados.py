"""
Comando para limpar dados de teste do banco.
Uso: python manage.py limpar_dados
"""

from django.core.management.base import BaseCommand

from finance.models import DailyClosing, Expense


class Command(BaseCommand):
    help = "Limpa todos os dados de teste (fechamentos e despesas)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirmar",
            action="store_true",
            help="Confirma a exclusão sem pedir confirmação",
        )

    def handle(self, *args, **options):
        # Contar registros
        total_closings = DailyClosing.objects.count()
        total_expenses = Expense.objects.count()

        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(self.style.WARNING("ATENÇÃO: VOCÊ ESTÁ PRESTES A EXCLUIR DADOS"))
        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write("")
        self.stdout.write(f"📊 Fechamentos a excluir: {total_closings}")
        self.stdout.write(f"💰 Despesas a excluir: {total_expenses}")
        self.stdout.write("")

        if total_closings == 0 and total_expenses == 0:
            self.stdout.write(self.style.SUCCESS("✓ Não há dados para excluir!"))
            return

        # Confirmar
        if not options["confirmar"]:
            resposta = input(
                '\nDeseja realmente excluir TODOS os dados? (digite "SIM" para confirmar): '
            )
            if resposta != "SIM":
                self.stdout.write(self.style.WARNING("Operação cancelada."))
                return

        # Excluir
        self.stdout.write("")
        self.stdout.write("Excluindo dados...")

        expenses_deleted, _ = Expense.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✓ {total_expenses} despesas excluídas"))

        closings_deleted, _ = DailyClosing.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"✓ {total_closings} fechamentos excluídos"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("DADOS EXCLUÍDOS COM SUCESSO!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write("Agora você pode:")
        self.stdout.write("1. Criar novos dados manualmente via interface")
        self.stdout.write("2. Executar: python criar_dados_teste.py")
        self.stdout.write("")
