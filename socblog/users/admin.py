from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, post

User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    pass

@admin.register(post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    search_fields = ('content',)
    list_filter = ('created_at',)