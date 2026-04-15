from django.contrib import admin
from .models import Project, Module, Config, TestCase, DDTSource


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_by', 'created_at', 'updated_at']
    search_fields = ['name', 'description']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'description', 'created_at', 'updated_at']
    list_filter = ['project']
    search_fields = ['name', 'description']


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'module', 'env_type', 'created_by', 'created_at', 'updated_at']
    list_filter = ['env_type', 'module__project']
    search_fields = ['name']


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'module', 'method', 'is_parameterized', 'ddt_source', 'created_by', 'updated_at']
    list_filter = ['method', 'is_parameterized', 'module__project']
    search_fields = ['name', 'url']


@admin.register(DDTSource)
class DDTSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'description', 'created_at', 'updated_at']
    list_filter = ['source_type']
    search_fields = ['name']
