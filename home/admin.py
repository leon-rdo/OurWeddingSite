from django.contrib import admin
from django.forms import TextInput
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
    list_display = ('title', 'featured', 'position', 'hide', 'hide_title')
    search_fields = ('title', 'description')
    list_filter = ('featured', 'position', 'hide', 'hide_title')
    actions = ['hide_selected_galleries']

    def hide_selected_galleries(self, request, queryset):
        queryset.update(hide=True)
    hide_selected_galleries.short_description = "Ocultar galerias selecionadas"


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


class GuestNameFilter(admin.SimpleListFilter):
    title = 'Escolhido?'
    parameter_name = 'guest_name'

    def lookups(self, request, model_admin):
        return (
            ('with_guest', 'Escolhido'),
            ('without_guest', 'Não-Escolhido'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'with_guest':
            return queryset.exclude(guest_name__isnull=True).exclude(guest_name__exact='')
        if self.value() == 'without_guest':
            return queryset.filter(guest_name__isnull=True) | queryset.filter(guest_name__exact='')

@admin.register(BridalShowerGift)
class BridalShowerGiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'guest_name')
    search_fields = ('name', 'description', 'price', 'guest_name', 'guest_phone', 'guest_email')
    inlines = [BridalShowerGiftSuggestionInline]
    list_filter = ('category', GuestNameFilter, 'way_to_gift', 'colors')
    actions = ['send_reminder_for_gift']
    fieldsets = (
        ('Presente', {
            'fields': ('name', 'description', 'image', 'category', 'price', 'colors')
        }),
        ('Convidado', {
            'fields': ('way_to_gift', 'guest_name', 'guest_phone', 'guest_email'),
            'classes': ('collapse',)
        })
    )

    def send_reminder_for_gift(self, request, queryset):
        for gift in queryset:
            if gift.guest_phone:
                settings = Settings.objects.first()
                datetime = settings.bridal_shower_datetime.strftime("%d/%m/%Y às %Hh%M")
                message = f'Você escolheu o presente "{gift.name}"\n\nObrigado por confirmar este presente!\n\nLembrando que o chá de panela será em {datetime}.\n\nEstamos muito gratos de saber que você estará nos ajudando em nossa nova jornada, obrigado!\n\nConfira os detalhes sobre as características do seu presente e outras informações importantes:\nhttps://weddingbliss.site/cha-de-panela/?phone={gift.guest_phone}'
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/{gift.guest_phone}?text={encoded_message}"
                self.message_user(request, format_html(
                    '<a href="{}" target="_blank">Clique aqui para enviar a mensagem para {}</a>', whatsapp_url, gift.guest_name
                ))

    send_reminder_for_gift.short_description = "Enviar lembrete via WhatsApp"


@admin.register(BridalShowerGiftColor)
class BridalShowerGiftColorAdmin(admin.ModelAdmin):
    
    from django.forms import ModelForm

    class BridalShowerGiftColorForm(ModelForm):
        class Meta:
            model = BridalShowerGiftColor
            fields = '__all__'
            widgets = {
                'color': TextInput(attrs={'type': 'color'}),
            }

    list_display = ('name', 'color')
    search_fields = ('name', 'color')
    form = BridalShowerGiftColorForm
