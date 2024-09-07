from django.contrib import admin
from .models import Settings, TextContent, Gallery


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('couple_names', 'wedding_datetime', 'ceremony_address', 'reception_address')
    search_fields = ('couple_names',)


@admin.register(TextContent)
class TextContentAdmin(admin.ModelAdmin):
    list_display = ('position', 'title')
    search_fields = ('title', 'content')
    list_filter = ('position',)


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'featured', 'position')
    search_fields = ('title', 'description')
    list_filter = ('featured', 'position')