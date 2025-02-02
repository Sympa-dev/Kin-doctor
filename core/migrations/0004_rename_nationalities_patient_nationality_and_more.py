# Generated by Django 5.1.4 on 2025-01-26 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_patient_company'),
    ]

    operations = [
        migrations.RenameField(
            model_name='patient',
            old_name='nationalities',
            new_name='nationality',
        ),
        migrations.AlterField(
            model_name='patient',
            name='marital_status',
            field=models.CharField(blank=True, choices=[('Single', 'Célibataire'), ('Married', 'Marié(e)'), ('Widowed', 'Veuf(vue)'), ('Divorced', 'Divorcé(e)')], max_length=10, null=True),
        ),
    ]
