"""
Management command para criar superusuário automaticamente no deploy.
"""

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cria superusuário automaticamente se não existir"

    def handle(self, *args, **options):
        # Verificar se já existe algum superusuário
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING("Superusuário já existe. Pulando criação."))
            return

        # Pegar credenciais das variáveis de ambiente
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")

        # Criar superusuário
        try:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Superusuário criado com sucesso!\n"
                    f"   Username: {username}\n"
                    f"   Email: {email}\n"
                    f"   Senha: {password}"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao criar superusuário: {e}"))
