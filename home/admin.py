from django.contrib import admin
from django.urls import reverse_lazy
from .models import *
from django.utils.html import format_html
from .models import Guest
import urllib.parse


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('couple_names', 'wedding_datetime', 'ceremony_address', 'reception_address')
    search_fields = ('couple_names',)


class GalleryInline(admin.TabularInline):
    model = Gallery
    extra = 1
    fields = ('title', 'description', 'image')


@admin.register(TextContent)
class TextContentAdmin(admin.ModelAdmin):
    list_display = ('position', 'title')
    search_fields = ('title', 'content')
    list_filter = ('position',)
    inlines = [GalleryInline]


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
    actions = ['send_thank_you_message']

    def send_thank_you_message(self, request, queryset):
        for guest in queryset:
            if guest.phone:
                settings = Settings.objects.first()
                datetime = settings.wedding_datetime.strftime("%d/%m/%Y às %Hh%M")
                gift_list_url = settings.site_url + reverse_lazy('home:gift_list')
                message = f"Obrigado por confirmar sua presença!\n\nLembrando que a cerimônia começará pontualmente em {datetime}.\n\nNão deixe de conferir também a lista de presentes no nosso site!\n\nEstamos muito alegres de saber que você estará conosco neste dia tão especial!\n\nAté lá!!!\n\n{gift_list_url}"
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/{guest.phone}?text={encoded_message}"
                self.message_user(request, format_html(
                    '<a href="{}" target="_blank">Clique aqui para enviar a mensagem para {}</a>', whatsapp_url, guest.name
                ))

    send_thank_you_message.short_description = "Enviar mensagem de agradecimento via WhatsApp"


class BridalShowerGiftSuggestionInline(admin.TabularInline):
    model = BridalShowerGiftSuggestion
    extra = 1
    fields = ('name', 'link')


@admin.register(BridalShowerGift)
class BridalShowerGiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'category')
    search_fields = ('name', 'description')
    inlines = [BridalShowerGiftSuggestionInline]
    list_filter = ('category',)
    fieldsets = (
        ('Gift', {
            'fields': ('name', 'description', 'image', 'category')
        }),
        ('Guest', {
            'fields': ('guest_name', 'guest_phone', 'guest_email'),
            'classes': ('collapse',)
        })
    )