from django.db import migrations


def create_operacao_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Operacao')


def remove_operacao_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Operacao').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0002_orders_and_items'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_operacao_group, remove_operacao_group),
    ]
