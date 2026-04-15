from django.contrib import admin
from .models import Project, Module, Config


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
