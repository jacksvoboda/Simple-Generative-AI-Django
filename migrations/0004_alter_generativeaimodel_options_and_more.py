# pylint: skip-file
# Generated by Django 4.2.11 on 2024-04-26 18:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simple_generative_ai', '0003_generativeaimodelrequest'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='generativeaimodel',
            options={'verbose_name': 'Generative AI model', 'verbose_name_plural': 'Generative AI models'},
        ),
        migrations.AlterModelOptions(
            name='generativeaimodelrequest',
            options={'verbose_name': 'Generative AI model request log', 'verbose_name_plural': 'Generative AI request logs'},
        ),
    ]
