# Generated by Django 4.2.7 on 2024-01-15 04:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_alter_customuser_managers_thread_model_thread_prompt_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thread',
            name='model',
            field=models.CharField(choices=[('gpt-4', 'gpt-4'), ('gpt-3.5-turbo-16k', 'gpt-3.5-turbo-16k'), ('gpt-3.5-turbo', 'gpt-3.5-turbo')], default='gpt-3.5-turbo', max_length=20),
        ),
    ]
