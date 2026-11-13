from django.contrib import admin
from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Konfiguracja panelu administracyjnego dla modelu Game."""

    list_display = (
        'title',
        'genre',
        'platform',
        'release_year',
        'rating',
        'status',
        'is_multiplayer',
        'created_at',
    )
    list_filter = ('status', 'is_multiplayer', 'platform', 'genre', 'release_year')
    search_fields = ('title', 'genre', 'platform', 'description')
    list_editable = ('rating', 'status', 'platform')
    ordering = ('-release_year', 'title')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('title', 'genre', 'release_year', 'description'),
        }),
        ('Szczegóły i ocena', {
            'fields': ('platform', 'status', 'rating', 'is_multiplayer', 'created_at'),
        }),
    )
