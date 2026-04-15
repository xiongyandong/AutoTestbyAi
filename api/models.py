from django.db import models


class Project(models.Model):
    name = models.CharField('项目名称', max_length=100, unique=True)
    description = models.TextField('项目描述', blank=True, default='')
    created_by = models.CharField('创建人', max_length=50, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class Module(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='所属项目', related_name='modules')
    name = models.CharField('模块名称', max_length=100)
    description = models.TextField('模块描述', blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '模块'
        verbose_name_plural = verbose_name
        ordering = ['project', 'name']
        unique_together = [['project', 'name']]

    def __str__(self):
        return f'{self.project.name} / {self.name}'


class Config(models.Model):
    ENV_CHOICES = [
        ('DEV', '开发环境'),
        ('QA', '测试环境'),
        ('PROD', '生产环境'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, verbose_name='所属模块', related_name='configs')
    name = models.CharField('配置名称', max_length=100)
    variables = models.JSONField('全局变量', default=dict, blank=True)
    parameters = models.JSONField('公共请求参数', default=dict, blank=True)
    request_hooks = models.JSONField('请求Hooks', default=dict, blank=True)
    response_hooks = models.JSONField('响应Hooks', default=dict, blank=True)
    env_type = models.CharField('环境类型', max_length=10, choices=ENV_CHOICES, default='DEV')
    created_by = models.CharField('创建人', max_length=50, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '配置'
        verbose_name_plural = verbose_name
        ordering = ['module', 'name']

    def __str__(self):
        return f'{self.module} / {self.name}'
