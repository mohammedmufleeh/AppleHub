# Generated by Django 4.0.6 on 2022-08-10 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_rename_payment_id_payment_payment_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(default='razorpay', max_length=100),
        ),
    ]
