from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from home.models import *
import base64
from io import BytesIO
import crcmod
import qrcode


class IndexView(TemplateView):
    template_name = "home/index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["intro_text"] = TextContent.objects.filter(position="intro").first()
        context["text_1"] = TextContent.objects.filter(position="text_1").first()
        context["text_2"] = TextContent.objects.filter(position="text_2").first()
        context["text_3"] = TextContent.objects.filter(position="text_3").first()
        context["text_4"] = TextContent.objects.filter(position="text_4").first()
        context["text_5"] = TextContent.objects.filter(position="text_5").first()
        context["leave_a_message_text"] = TextContent.objects.filter(position="leave_a_message_text").first()
        context["leave_a_message_text2"] = TextContent.objects.filter(position="leave_a_message_text2").first()
        context["last_text"] = TextContent.objects.filter(position="last_text").first()
        context["featured_circles"] = Gallery.objects.filter(featured=True, position="circles").all()
        context["featured_gallery"] = Gallery.objects.filter(featured=True, position="gallery").all()
        return context


class AboutUsView(TemplateView):
    template_name = "home/about-us.html"

    def get_context_data(self, **kwargs):
        context = super(AboutUsView, self).get_context_data(**kwargs)
        context["about_us_text_1"] = TextContent.objects.filter(position="about_us_text_1").first()
        context["about_us_text_2"] = TextContent.objects.filter(position="about_us_text_2").first()
        context["about_us_text_3"] = TextContent.objects.filter(position="about_us_text_3").first()
        context["about_us_text_4"] = TextContent.objects.filter(position="about_us_text_4").first()
        context["about_us_text_5"] = TextContent.objects.filter(position="about_us_text_5").first()
        return context


class GalleryView(UserPassesTestMixin, TemplateView):
    template_name = "home/gallery.html"

    def test_func(self):
        if not Settings.objects.first().hide_gallery:
            return True
        else:
            return self.request.user.has_perm('home.view_gallery')

    def get_context_data(self, **kwargs):
        context = super(GalleryView, self).get_context_data(**kwargs)
        context["gallery_text_1"] = TextContent.objects.filter(position="gallery_text_1").first()
        context["gallery_text_2"] = TextContent.objects.filter(position="gallery_text_2").first()
        context["gallery"] = Gallery.objects.all()
        return context


class Payload():
    def __init__(self, nome, chavepix, valor, cidade, txtId, diretorio=''):
        self.nome = nome
        self.chavepix = chavepix
        self.valor = valor.replace(',', '.')
        self.cidade = cidade
        self.txtId = txtId
        self.diretorioQrCode = diretorio

        self.nome_tam = len(self.nome)
        self.chavepix_tam = len(self.chavepix)
        self.valor_tam = len(self.valor)
        self.cidade_tam = len(self.cidade)
        self.txtId_tam = len(self.txtId)

        self.merchantAccount_tam = f'0014BR.GOV.BCB.PIX01{self.chavepix_tam:02}{self.chavepix}'
        self.transactionAmount_tam = f'{self.valor_tam:02}{float(self.valor):.2f}'

        self.addDataField_tam = f'05{self.txtId_tam:02}{self.txtId}'

        self.nome_tam = f'{self.nome_tam:02}'

        self.cidade_tam = f'{self.cidade_tam:02}'

        self.payloadFormat = '000201'
        self.merchantAccount = f'26{len(self.merchantAccount_tam):02}{self.merchantAccount_tam}'
        self.merchantCategCode = '52040000'
        self.transactionCurrency = '5303986'
        self.transactionAmount = f'54{self.transactionAmount_tam}'
        self.countryCode = '5802BR'
        self.merchantName = f'59{self.nome_tam:02}{self.nome}'
        self.merchantCity = f'60{self.cidade_tam:02}{self.cidade}'
        self.addDataField = f'62{len(self.addDataField_tam):02}{self.addDataField_tam}'
        self.crc16 = '6304'

    def gerarPayload(self):
        self.payload = f'{self.payloadFormat}{self.merchantAccount}{self.merchantCategCode}{self.transactionCurrency}{self.transactionAmount}{self.countryCode}{self.merchantName}{self.merchantCity}{self.addDataField}{self.crc16}'
        self.gerarCrc16(self.payload)

    def gerarCrc16(self, payload):
        crc16 = crcmod.mkCrcFun(poly=0x11021, initCrc=0xFFFF, rev=False, xorOut=0x0000)
        self.crc16Code = hex(crc16(str(payload).encode('utf-8')))
        self.crc16Code_formatado = str(self.crc16Code).replace('0x', '').upper().zfill(4)
        self.payload_completa = f'{payload}{self.crc16Code_formatado}'
        self.gerarQrCode(self.payload_completa, self.diretorioQrCode)

    def gerarQrCode(self, payload, diretorio):
        qr = qrcode.make(payload)
        buffered = BytesIO()
        qr.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return qr_code_base64


class GiftListView(UserPassesTestMixin, ListView):
    template_name = "home/gift-list.html"
    model = Gift

    def test_func(self):
        if not Settings.objects.first().hide_gifts:
            return True
        else:
            return self.request.user.has_perm('home.view_gift')

    def get_context_data(self, **kwargs):
        context = super(GiftListView, self).get_context_data(**kwargs)
        context["gift_list_text"] = TextContent.objects.filter(position="gift_list_text").first()
        
        settings = Settings.objects.first()
        for gift in context['object_list']:
            if settings.account_holder and settings.pix_key and gift.price:
                payload = Payload(
                    nome=settings.account_holder,
                    chavepix=settings.pix_key,
                    valor=str(gift.price),
                    cidade="Belem",
                    txtId=str(gift.id),
                    diretorio=''
                )
                payload.gerarPayload()
                gift.qr_code = payload.gerarQrCode(payload.payload_completa, '')
            else:
                gift.qr_code = None

        return context


class MessageFormView(View):
    def post(self, request):
        form = request.POST
        message = Message.objects.create(
            name=form['name'],
            message=form['message']
        )
        message.save()
        return JsonResponse({'message': 'Obrigado! Sua mensagem foi enviada.'})


class RSVPFormView(UserPassesTestMixin, TemplateView):
    template_name = "home/rsvp.html"

    def test_func(self):
        if not Settings.objects.first().hide_rsvp:
            return True
        else:
            return self.request.user.has_perm('home.view_guest')

    def post(self, request, *args, **kwargs):
        phone_number = request.POST.get('phone_number')
        action = request.POST.get('action')

        if action == 'check_phone':
            guests = Guest.objects.filter(phone=phone_number)
            if guests.exists():
                if guests.count() > 1:
                    guest_names = list(guests.values_list('name', flat=True))
                    return JsonResponse({'multiple': True, 'names': guest_names})
                else:
                    guest = guests.first()
                    return JsonResponse({'exists': True, 'name': guest.name})
            else:
                return JsonResponse({'exists': False})
        
        elif action == 'confirm_name':
            name = request.POST.get('name')
            guest = Guest.objects.get(phone=phone_number, name=name)
            return JsonResponse({'confirmed': True})
        
        elif action == 'create_guest':
            name = request.POST.get('name')
            guest = Guest.objects.create(name=name, phone=phone_number, self_created=True)
            return JsonResponse({'guest_created': True})
        
        elif action == 'submit_rsvp':
            name = request.POST.get('name')

            if not name:
                return JsonResponse({'error': 'Name is required for RSVP'}, status=400)

            try:
                # Buscar o convidado pelo telefone e nome
                guest = Guest.objects.get(phone=phone_number, name=name)
                will_go = request.POST.get('will_go') == 'yes'
                guest.will_go = will_go
                guest.save()
                return JsonResponse({'rsvp_submitted': True})
            except Guest.DoesNotExist:
                return JsonResponse({'error': 'Guest not found'}, status=404)
            except Guest.MultipleObjectsReturned:
                return JsonResponse({'error': 'Multiple guests found with the same name and phone'}, status=400)

        return JsonResponse({'error': 'Invalid action'}, status=400)


class BridalShowerGiftListView(UserPassesTestMixin, ListView):
    template_name = "home/bridal-shower-gift-list.html"
    model = BridalShowerGift

    def test_func(self):
        if not Settings.objects.first().hide_bridal_shower_gift:
            return True
        else:
            return self.request.user.has_perm('home.view_bridalshowergift')

    def get_context_data(self, **kwargs):
        context = super(BridalShowerGiftListView, self).get_context_data(**kwargs)
        context["bridal_shower_text"] = TextContent.objects.filter(position="bridal_shower_text").first()
        return context