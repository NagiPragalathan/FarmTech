# Generated by Django 3.2.15 on 2022-08-30 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_alter_profile_profileimg'),
    ]

    operations = [
        migrations.CreateModel(
            name='Emergency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(max_length=100)),
                ('number', models.CharField(max_length=100)),
                ('messages', models.CharField(default='i am in trubble please help me', max_length=100)),
            ],
        ),
    ]
