import base64
import json
from datetime import datetime
from io import BytesIO

import crcmod
import mercadopago
import qrcode
from django.conf import settings as django_settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView

from home.models import Gift, BridalShowerGift, TextContent, Gallery, Settings, Message, Guest, Payment


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
        context["gallery"] = Gallery.objects.filter(hide=False)
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
        context["MERCADO_PAGO_PUBLIC_KEY"] = django_settings.MERCADO_PAGO_PUBLIC_KEY
        
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
                gift.payload = payload.payload_completa
            else:
                gift.qr_code = None
                gift.payload = None

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
    
    def get_queryset(self):
        gifts = super(BridalShowerGiftListView, self).get_queryset()

        email = self.request.GET.get('email')
        phone = self.request.GET.get('phone')
        
        if phone and email:
            return gifts.filter(guest_phone=phone) | gifts.filter(guest_email=email)
        elif phone:
            phone = phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            return gifts.filter(guest_phone=phone)
        elif email:
            return gifts.filter(guest_email=email)
        else:
            return gifts.filter(guest_name__isnull=True)

    def get_context_data(self, **kwargs):
        context = super(BridalShowerGiftListView, self).get_context_data(**kwargs)
        context["bridal_shower_text"] = TextContent.objects.filter(position="bridal_shower_text").first()
        
        email = self.request.GET.get('email')
        phone = self.request.GET.get('phone')

        if phone or email:
            settings = Settings.objects.first()
            for gift in context['object_list']:
                if gift.price:
                    payload = Payload(
                        nome=settings.account_holder,
                        chavepix=settings.pix_key,
                        valor=str(gift.price),
                        cidade="Belem",
                        txtId=str(gift.id),
                        diretorio=''
                    )
                    payload.gerarPayload()
                    qr_code_base64 = payload.gerarQrCode(payload.payload_completa, '')

                    # Passar o QR code gerado para o contexto de cada presente
                    gift.qr_code = qr_code_base64
                    gift.payload = payload.payload_completa
        return context

    def post(self, request, *args, **kwargs):
        way_to_gift = request.POST.get('way_to_gift')
        guest_name = request.POST.get('name')
        guest_email = request.POST.get('email')
        guest_phone = request.POST.get('phone_number')
        guest_phone = guest_phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        gift_id = request.POST.get('gift_id')
        gift = get_object_or_404(BridalShowerGift, id=gift_id)
        gift.way_to_gift = way_to_gift
        gift.guest_name = guest_name
        gift.guest_email = guest_email
        gift.guest_phone = guest_phone
        gift.save()
        if way_to_gift == 'money':
            messages.success(request, f'Presente {gift.name} escolhido com sucesso! Confira o pix')
            return HttpResponseRedirect(reverse('home:bridal_shower_gift_list') + f'?phone={guest_phone}&email={guest_email}&gift={gift_id}')
        else:
            messages.success(request, f'Presente {gift.name} escolhido com sucesso!')
            return HttpResponseRedirect(reverse('home:bridal_shower_gift_list') + f'?phone={guest_phone}&email={guest_email}')


class CreatePaymentView(View):
    """
    View para criar preferência de pagamento no Mercado Pago
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            gift_type = data.get('gift_type')
            gift_id = data.get('gift_id')
            buyer_name = data.get('buyer_name')
            buyer_email = data.get('buyer_email')
            amount = data.get('amount')
            
            sdk = mercadopago.SDK(django_settings.MERCADO_PAGO_ACCESS_TOKEN)
            
            if gift_type == 'gift':
                gift = get_object_or_404(Gift, id=gift_id)
            else:
                gift = get_object_or_404(BridalShowerGift, id=gift_id)
            
            if not amount:
                payment_amount = float(gift.remaining_amount if hasattr(gift, 'remaining_amount') else gift.price)
            else:
                payment_amount = float(amount)
            
            preference_data = {
                "items": [
                    {
                        "title": gift.name,
                        "description": gift.description[:255],
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": payment_amount
                    }
                ],
                "payer": {
                    "name": buyer_name,
                    "email": buyer_email,
                },
                "back_urls": {
                    "success": f"{django_settings.SITE_URL}/pagamento/sucesso/",
                    "failure": f"{django_settings.SITE_URL}/pagamento/falha/",
                    "pending": f"{django_settings.SITE_URL}/pagamento/pendente/"
                },
                "auto_return": "approved",
                "notification_url": f"{django_settings.SITE_URL}/webhook/mercadopago/",
                "external_reference": f"{gift_type}_{gift_id}_{buyer_email}",
                "statement_descriptor": "PRESENTE CASAMENTO",
                "payment_methods": {
                    "excluded_payment_types": [],
                    "installments": 12
                }
            }
            
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response["response"]
            
            return JsonResponse({
                'status': 'success',
                'preference_id': preference['id'],
                'init_point': preference['init_point']
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


class ProcessPaymentView(View):
    """
    View para processar pagamento com cartão via checkout transparente
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            sdk = mercadopago.SDK(django_settings.MERCADO_PAGO_ACCESS_TOKEN)
            
            gift_type = data.get('gift_type')
            gift_id = data.get('gift_id')
            amount = data.get('amount')
            
            if gift_type == 'gift':
                gift = get_object_or_404(Gift, id=gift_id)
            else:
                gift = get_object_or_404(BridalShowerGift, id=gift_id)
            
            if not amount:
                payment_amount = float(gift.remaining_amount if hasattr(gift, 'remaining_amount') else gift.price)
            else:
                payment_amount = float(amount)
            
            payment_data = {
                "transaction_amount": payment_amount,
                "token": data.get('token'),
                "description": gift.name,
                "installments": int(data.get('installments', 1)),
                "payment_method_id": data.get('payment_method_id'),
                "issuer_id": data.get('issuer_id'),
                "payer": {
                    "email": data.get('email'),
                    "identification": {
                        "type": data.get('identification_type'),
                        "number": data.get('identification_number')
                    }
                },
                "notification_url": f"{django_settings.SITE_URL}/webhook/mercadopago/",
                "external_reference": f"{gift_type}_{gift_id}_{data.get('email')}",
                "statement_descriptor": "PRESENTE CASAMENTO"
            }
            
            payment_response = sdk.payment().create(payment_data)
            payment = payment_response["response"]
            
            if 'id' not in payment:
                error_message = payment.get('message', 'Unknown error creating payment')
                return JsonResponse({
                    'status': 'error',
                    'message': error_message
                }, status=400)
            
            content_type = ContentType.objects.get_for_model(gift)
            Payment.objects.create(
                content_type=content_type,
                object_id=gift.id,
                payment_id=str(payment['id']),
                payment_status=payment['status'],
                payer_name=data.get('payer_name', ''),
                payer_email=data.get('email', ''),
                payer_phone=data.get('phone', ''),
                amount=payment_amount,
                payment_method=payment.get('payment_method_id', ''),
                installments=int(data.get('installments', 1)),
                payment_date=datetime.now() if payment['status'] == 'approved' else None
            )
            
            return JsonResponse({
                'status': 'success',
                'payment_id': payment['id'],
                'status_detail': payment['status'],
                'status_message': payment.get('status_detail', '')
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class MercadoPagoWebhookView(View):
    """
    View para receber notificações do Mercado Pago sobre status de pagamentos
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            if data.get('type') == 'payment':
                payment_id = str(data['data']['id'])
                
                sdk = mercadopago.SDK(django_settings.MERCADO_PAGO_ACCESS_TOKEN)
                
                payment_info = sdk.payment().get(payment_id)
                payment_data = payment_info["response"]
                
                try:
                    payment = Payment.objects.get(payment_id=payment_id)
                    payment.payment_status = payment_data['status']
                    if payment_data['status'] == 'approved' and not payment.payment_date:
                        payment.payment_date = datetime.now()
                    payment.save()
                except Payment.DoesNotExist:
                    external_ref = payment_data.get('external_reference', '')
                    if external_ref:
                        parts = external_ref.split('_')
                        if len(parts) >= 2:
                            gift_type = parts[0]
                            gift_id = parts[1]
                            
                            if gift_type == 'gift':
                                gift = Gift.objects.get(id=gift_id)
                            else:
                                gift = BridalShowerGift.objects.get(id=gift_id)
                            
                            content_type = ContentType.objects.get_for_model(gift)
                            Payment.objects.create(
                                content_type=content_type,
                                object_id=gift.id,
                                payment_id=payment_id,
                                payment_status=payment_data['status'],
                                payer_name=payment_data.get('payer', {}).get('first_name', ''),
                                payer_email=payment_data.get('payer', {}).get('email', ''),
                                amount=payment_data.get('transaction_amount', 0),
                                payment_method=payment_data.get('payment_method_id', ''),
                                installments=payment_data.get('installments', 1),
                                payment_date=datetime.now() if payment_data['status'] == 'approved' else None
                            )
            
            return HttpResponse(status=200)
            
        except Exception as e:
            print(f"Erro no webhook: {str(e)}")
            return HttpResponse(status=200)
    
    def get(self, request):
        return HttpResponse(status=200)


class PaymentStatusView(View):
    """
    View para verificar status de um pagamento
    """
    
    def get(self, request, payment_id):
        try:
            sdk = mercadopago.SDK(django_settings.MERCADO_PAGO_ACCESS_TOKEN)
            payment_info = sdk.payment().get(payment_id)
            payment = payment_info["response"]
            
            return JsonResponse({
                'status': payment['status'],
                'status_detail': payment.get('status_detail', ''),
                'transaction_amount': payment['transaction_amount']
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
