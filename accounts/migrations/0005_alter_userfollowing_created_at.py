# Generated by Django 5.1.7 on 2025-03-13 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_userfollowing_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userfollowing',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
