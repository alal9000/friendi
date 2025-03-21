# Generated by Django 5.0.6 on 2025-02-27 03:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_statusupdate'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Reaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reaction_type', models.CharField(choices=[('heart', '❤️'), ('laugh', '😂'), ('fire', '🔥')], max_length=10)),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='app.statusupdate')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'status')},
            },
        ),
    ]
