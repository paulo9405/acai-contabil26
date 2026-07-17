from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_orderitem_item_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='idempotency_key',
            field=models.UUIDField(blank=True, null=True, unique=True, verbose_name='Chave de idempotência'),
        ),
    ]
