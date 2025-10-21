from django.contrib import admin
from .models import AnalyzedString

@admin.register(AnalyzedString)
class AnalyzedStringAdmin(admin.ModelAdmin):
    list_display = (
        'value',
        'length',
        'is_palindrome',
        'unique_characters',
        'word_count',
        'sha256_hash',
        'created_at',
    )
    search_fields = ('value', 'sha256_hash')
    readonly_fields = (
        'length',
        'is_palindrome',
        'unique_characters',
        'word_count',
        'sha256_hash',
        'character_frequency_map',
        'created_at',
    )
    ordering = ('-created_at',)