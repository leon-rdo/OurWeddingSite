from django.contrib import admin
from .models import Settings, TextContent, Gallery, Gift, Message, Guest


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


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'message')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'will_go', 'self_created')
    search_fields = ('name', 'phone')
    list_filter = ('will_go', 'self_created')
