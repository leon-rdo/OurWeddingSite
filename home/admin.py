from django.contrib import admin
from django.forms import TextInput
from django.urls import reverse_lazy
from unfold.admin import ModelAdmin, TabularInline, GenericTabularInline
from .models import *
from django.utils.html import format_html
from .models import Guest
import urllib.parse


@admin.register(Settings)
class SettingsAdmin(ModelAdmin):
    list_display = ('couple_names', 'wedding_datetime', 'ceremony_address', 'reception_address')
    search_fields = ('couple_names',)


class GalleryInline(TabularInline):
    model = Gallery
    extra = 1
    fields = ('title', 'description', 'image')


@admin.register(TextContent)
class TextContentAdmin(ModelAdmin):
    list_display = ('position', 'title')
    search_fields = ('title', 'content')
    list_filter = ('position',)
    inlines = [GalleryInline]


@admin.register(Gallery)
class GalleryAdmin(ModelAdmin):
    list_display = ('title', 'featured', 'position', 'hide', 'hide_title')
    search_fields = ('title', 'description')
    list_filter = ('featured', 'position', 'hide', 'hide_title')
    actions = ['hide_selected_galleries']

    def hide_selected_galleries(self, request, queryset):
        queryset.update(hide=True)
    hide_selected_galleries.short_description = "Ocultar galerias selecionadas"


class PaymentInline(GenericTabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_id', 'payment_status', 'payer_name', 'payer_email', 'amount', 'payment_date', 'created_at')
    fields = ('payment_id', 'payer_name', 'payer_email', 'amount', 'payment_status', 'payment_date')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Gift)
class GiftAdmin(ModelAdmin):
    list_display = ('name', 'description', 'price', 'total_paid_display', 'remaining_display', 'payment_status_display')
    search_fields = ('name', 'description')
    inlines = [PaymentInline]
    
    fieldsets = (
        ('Informações do Presente', {
            'fields': ('name', 'description', 'image', 'price')
        }),
    )
    
    def total_paid_display(self, obj):
        total = obj.total_paid
        return f'R$ {total:.2f}'
    total_paid_display.short_description = 'Total Pago'
    
    def remaining_display(self, obj):
        remaining = obj.remaining_amount
        if remaining <= 0:
            return format_html('<span style="color: green; font-weight: bold;">✓ Pago</span>')
        return f'R$ {remaining:.2f}'
    remaining_display.short_description = 'Restante'
    
    def payment_status_display(self, obj):
        if obj.is_fully_paid:
            return format_html('<span style="color: green; font-weight: bold;">✓ Completo</span>')
        elif obj.total_paid > 0:
            return format_html('<span style="color: orange;">⚠ Parcial</span>')
        return format_html('<span style="color: gray;">- Pendente</span>')
    payment_status_display.short_description = 'Status'


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'message')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(Guest)
class GuestAdmin(ModelAdmin):
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


class BridalShowerGiftSuggestionInline(TabularInline):
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
class BridalShowerGiftAdmin(ModelAdmin):
    list_display = ('name', 'category', 'guest_name', 'total_paid_display', 'remaining_display', 'payment_status_display')
    search_fields = ('name', 'description', 'price', 'guest_name', 'guest_phone', 'guest_email')
    inlines = [BridalShowerGiftSuggestionInline, PaymentInline]
    list_filter = ('category', GuestNameFilter, 'way_to_gift', 'colors')
    actions = ['send_reminder_for_gift']
    
    fieldsets = (
        ('Presente', {
            'fields': ('name', 'description', 'image', 'category', 'price', 'colors')
        }),
        ('Convidado', {
            'fields': ('way_to_gift', 'guest_name', 'guest_phone', 'guest_email'),
            'classes': ('collapse',)
        }),
    )
    
    def total_paid_display(self, obj):
        if not obj.price:
            return '-'
        total = obj.total_paid
        return f'R$ {total:.2f}'
    total_paid_display.short_description = 'Total Pago'
    
    def remaining_display(self, obj):
        if not obj.price:
            return '-'
        remaining = obj.remaining_amount
        if remaining <= 0:
            return format_html('<span style="color: green; font-weight: bold;">✓ Pago</span>')
        return f'R$ {remaining:.2f}'
    remaining_display.short_description = 'Restante'
    
    def payment_status_display(self, obj):
        if not obj.price:
            return '-'
        if obj.is_fully_paid:
            return format_html('<span style="color: green; font-weight: bold;">✓ Completo</span>')
        elif obj.total_paid > 0:
            return format_html('<span style="color: orange;">⚠ Parcial</span>')
        return format_html('<span style="color: gray;">- Pendente</span>')
    payment_status_display.short_description = 'Pagamento'

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
class BridalShowerGiftColorAdmin(ModelAdmin):
    
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


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('payment_id', 'get_gift_name', 'payer_name', 'amount', 'payment_status', 'payment_date')
    search_fields = ('payment_id', 'payer_name', 'payer_email')
    list_filter = ('payment_status', 'payment_method', 'created_at')
    readonly_fields = ('content_type', 'object_id', 'payment_id', 'payment_status', 'payer_name', 
                      'payer_email', 'payer_phone', 'amount', 'payment_method', 'installments',
                      'created_at', 'payment_date', 'updated_at')
    
    def get_gift_name(self, obj):
        return str(obj.gift)
    get_gift_name.short_description = 'Presente'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
