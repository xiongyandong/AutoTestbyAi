from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_scriptasset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='config',
            name='request_hooks',
            field=models.JSONField(blank=True, default=list, verbose_name='请求Hooks'),
        ),
        migrations.AlterField(
            model_name='config',
            name='response_hooks',
            field=models.JSONField(blank=True, default=list, verbose_name='响应Hooks'),
        ),
    ]
