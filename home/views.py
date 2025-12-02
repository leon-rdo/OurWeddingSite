import base64
from datetime import datetime
from io import BytesIO
import json
import logging

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
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from home.models import Gift, BridalShowerGift, TextContent, Gallery, Settings, Message, Guest, Payment


logger = logging.getLogger('home')



def send_payment_confirmation_email(payment_obj, gift):
    """
    Envia e-mail de confirmação de pagamento
    """
    try:
        settings = Settings.objects.first()
        
        # Determinar tipo de presente
        gift_type = "Presente de Casamento"
        if isinstance(gift, BridalShowerGift):
            gift_type = "Presente de Chá de Panela"
        
        # Contexto para o template
        context = {
            'payment': payment_obj,
            'gift': gift,
            'gift_type': gift_type,
            'settings': settings,
            'site_url': django_settings.SITE_URL,
        }
        
        # Renderizar template HTML
        html_content = render_to_string('home/emails/payment_confirmation.html', context)
        text_content = strip_tags(html_content)
        
        # Criar e-mail
        subject = f'✅ Pagamento Confirmado - {gift.name}'
        from_email = django_settings.DEFAULT_FROM_EMAIL
        to_email = payment_obj.payer_email
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Enviar
        email.send()
        
        logger.info(f"E-mail de confirmação enviado para {to_email} - Pagamento: {payment_obj.payment_id}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail de confirmação: {str(e)}", exc_info=True)
        return False


def send_payment_pending_email(payment_obj, gift):
    """
    Envia e-mail informando que o pagamento está pendente
    """
    try:
        settings = Settings.objects.first()
        
        gift_type = "Presente de Casamento"
        if isinstance(gift, BridalShowerGift):
            gift_type = "Presente de Chá de Panela"
        
        context = {
            'payment': payment_obj,
            'gift': gift,
            'gift_type': gift_type,
            'settings': settings,
            'site_url': django_settings.SITE_URL,
        }
        
        html_content = render_to_string('home/emails/payment_pending.html', context)
        text_content = strip_tags(html_content)
        
        subject = f'⏳ Pagamento em Análise - {gift.name}'
        from_email = django_settings.DEFAULT_FROM_EMAIL
        to_email = payment_obj.payer_email
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"E-mail de pendência enviado para {to_email} - Pagamento: {payment_obj.payment_id}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail de pendência: {str(e)}", exc_info=True)
        return False

def get_friendly_payment_message(status_detail, status=None):
    """
    Converte status_detail do Mercado Pago em mensagens amigáveis
    """
    
    # Mensagens para status aprovados
    approved_messages = {
        'accredited': 'Pagamento aprovado e creditado! 🎉',
    }
    
    # Mensagens para status pendentes
    pending_messages = {
        'pending_contingency': 'Estamos processando seu pagamento. Em breve você receberá o resultado por e-mail.',
        'pending_review_manual': 'Seu pagamento está sendo analisado. Você receberá o resultado em até 2 dias úteis.',
        'pending_waiting_payment': 'Aguardando o pagamento ser processado.',
        'pending_waiting_transfer': 'Aguardando a transferência bancária.',
    }
    
    # Mensagens para status rejeitados - organizadas por tipo de problema
    rejected_messages = {
        # Problemas com o cartão
        'cc_rejected_bad_filled_card_number': 'Verifique o número do cartão e tente novamente.',
        'cc_rejected_bad_filled_date': 'Verifique a data de validade do cartão.',
        'cc_rejected_bad_filled_other': 'Verifique os dados do cartão e tente novamente.',
        'cc_rejected_bad_filled_security_code': 'Verifique o código de segurança (CVV) do cartão.',
        
        # Cartão inválido ou vencido
        'cc_rejected_blacklist': 'Não foi possível processar seu pagamento. Entre em contato com seu banco.',
        'cc_rejected_call_for_authorize': 'Entre em contato com seu banco para autorizar o pagamento.',
        'cc_rejected_card_disabled': 'Este cartão está desabilitado. Entre em contato com seu banco.',
        'cc_rejected_card_error': 'Não foi possível processar seu cartão. Tente com outro cartão.',
        'cc_rejected_duplicated_payment': 'Você já realizou um pagamento com esse valor recentemente. Se foi um erro, tente novamente em alguns minutos.',
        'cc_rejected_high_risk': 'Seu pagamento foi recusado por segurança. Entre em contato com seu banco.',
        'cc_rejected_insufficient_amount': 'Saldo ou limite insuficiente no cartão. Tente com outro cartão.',
        'cc_rejected_invalid_installments': 'O número de parcelas selecionado não está disponível. Escolha outra opção.',
        'cc_rejected_max_attempts': 'Você atingiu o limite de tentativas permitidas. Tente novamente em 24 horas.',
        'cc_rejected_other_reason': 'O pagamento foi recusado. Entre em contato com seu banco para mais informações.',
        
        # Problemas específicos
        'cc_amount_rate_limit_exceeded': 'Você excedeu o limite de pagamentos. Tente novamente mais tarde.',
        'rejected_insufficient_data': 'Alguns dados estão incompletos. Por favor, revise as informações.',
        'rejected_by_bank': 'Pagamento recusado pelo banco. Entre em contato com sua instituição financeira.',
        'rejected_by_regulations': 'Pagamento recusado por questões regulatórias. Entre em contato com seu banco.',
        
        # Genéricos
        'rejected_other_reason': 'Não foi possível processar o pagamento. Tente com outro método de pagamento.',
    }
    
    # Mensagens para cancelamentos
    cancelled_messages = {
        'cancelled': 'O pagamento foi cancelado.',
        'cc_rejected_cancelled': 'O pagamento foi cancelado.',
    }
    
    # Tentar encontrar mensagem específica
    if status == 'approved':
        return approved_messages.get(status_detail, 'Pagamento aprovado com sucesso! 🎉')
    
    if status == 'pending' or status == 'in_process':
        return pending_messages.get(
            status_detail, 
            'Seu pagamento está sendo processado. Você receberá uma confirmação em breve.'
        )
    
    if status == 'rejected':
        return rejected_messages.get(
            status_detail,
            'Pagamento não autorizado. Verifique os dados do cartão ou tente com outro método de pagamento.'
        )
    
    if status == 'cancelled':
        return cancelled_messages.get(status_detail, 'O pagamento foi cancelado.')
    
    # Mensagem genérica se não encontrar status específico
    return rejected_messages.get(
        status_detail,
        'Não foi possível processar o pagamento. Por favor, verifique seus dados e tente novamente.'
    )


def get_payment_suggestion(status_detail):
    """
    Retorna sugestões de ação baseadas no status_detail
    """
    suggestions = {
        # Problemas com dados do cartão
        'cc_rejected_bad_filled_card_number': 'Digite o número do cartão sem espaços ou caracteres especiais.',
        'cc_rejected_bad_filled_date': 'Verifique se o cartão não está vencido.',
        'cc_rejected_bad_filled_security_code': 'O código CVV tem 3 ou 4 dígitos e fica no verso do cartão.',
        
        # Problemas de limite/saldo
        'cc_rejected_insufficient_amount': 'Verifique seu saldo ou limite disponível com seu banco.',
        
        # Problemas de autorização
        'cc_rejected_call_for_authorize': 'Ligue para o número no verso do seu cartão antes de tentar novamente.',
        'cc_rejected_card_disabled': 'Seu cartão pode estar bloqueado. Entre em contato com o banco.',
        
        # Limite de tentativas
        'cc_rejected_max_attempts': 'Por segurança, aguarde 24 horas antes de nova tentativa.',
        
        # Problemas com banco
        'rejected_by_bank': 'Seu banco recusou a transação. Entre em contato com eles para entender o motivo.',
        
        # Pagamento duplicado
        'cc_rejected_duplicated_payment': 'Aguarde alguns minutos antes de tentar realizar o pagamento novamente.',
        
        # Parcelas inválidas
        'cc_rejected_invalid_installments': 'Tente escolher um número diferente de parcelas.',
        
        # Genérico
        'default': 'Tente usar outro cartão ou método de pagamento.',
    }
    
    return suggestions.get(status_detail, suggestions['default'])


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
        
        self.chavepix = self._formatar_chave_pix(chavepix)
        
        self.valor = valor.replace(',', '.')
        self.cidade = cidade
        self.txtId = txtId
        self.diretorioQrCode = diretorio

        self.nome_tam = len(self.nome)
        self.chavepix_tam = len(self.chavepix)
        self.valor_tam = len(self.valor)
        self.cidade_tam = len(self.cidade)
        self.txtId_tam = len(self.txtId)

        self.merchantAccount_tam = f'0014br.gov.bcb.pix01{self.chavepix_tam:02d}{self.chavepix}'
        
        self.transactionAmount_tam = f'{len(f"{float(self.valor):.2f}"):02d}{float(self.valor):.2f}'

        self.addDataField_tam = f'05{self.txtId_tam:02d}{self.txtId}'

        self.payloadFormat = '000201'
        self.merchantAccount = f'26{len(self.merchantAccount_tam):02d}{self.merchantAccount_tam}'
        self.merchantCategCode = '52040000'
        self.transactionCurrency = '5303986'
        self.transactionAmount = f'54{self.transactionAmount_tam}'
        self.countryCode = '5802BR'
        self.merchantName = f'59{self.nome_tam:02d}{self.nome}'
        self.merchantCity = f'60{self.cidade_tam:02d}{self.cidade}'
        self.addDataField = f'62{len(self.addDataField_tam):02d}{self.addDataField_tam}'
        self.crc16 = '6304'

    def _formatar_chave_pix(self, chave):
        """
        Formata a chave PIX corretamente:
        - Adiciona +55 para telefones brasileiros
        - Remove caracteres especiais
        - Mantém outros tipos de chave (email, CPF, CNPJ, aleatória)
        """
        chave_limpa = chave.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        
        if chave_limpa.isdigit() and len(chave_limpa) == 11:
            return f'+55{chave_limpa}'
        
        if chave_limpa.startswith('+55'):
            return chave_limpa
        
        if chave_limpa.startswith('55') and chave_limpa.isdigit() and len(chave_limpa) == 13:
            return f'+{chave_limpa}'
        
        if chave_limpa.replace('.', '').replace('-', '').replace('/', '').isdigit():
            return chave_limpa.replace('.', '').replace('-', '').replace('/', '')
        
        return chave_limpa.lower() if '@' in chave_limpa else chave_limpa

    def gerarPayload(self):
        """Gera o payload PIX completo"""
        self.payload = (
            f'{self.payloadFormat}'
            f'{self.merchantAccount}'
            f'{self.merchantCategCode}'
            f'{self.transactionCurrency}'
            f'{self.transactionAmount}'
            f'{self.countryCode}'
            f'{self.merchantName}'
            f'{self.merchantCity}'
            f'{self.addDataField}'
            f'{self.crc16}'
        )
        self.gerarCrc16(self.payload)
        return self.payload_completa

    def gerarCrc16(self, payload):
        """
        Calcula o CRC16 do payload PIX
        """
        crc16 = crcmod.mkCrcFun(poly=0x11021, initCrc=0xFFFF, rev=False, xorOut=0x0000)
        self.crc16Code = hex(crc16(str(payload).encode('utf-8')))
        self.crc16Code_formatado = str(self.crc16Code).replace('0x', '').upper().zfill(4)
        self.payload_completa = f'{payload}{self.crc16Code_formatado}'
        return self.payload_completa

    def gerarQrCode(self, payload, diretorio=''):
        """Gera o QR Code em base64"""
        qr = qrcode.make(payload)
        buffered = BytesIO()
        qr.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return qr_code_base64
    
    def obter_qrcode_base64(self):
        """Método helper para obter o QR Code após gerar o payload"""
        if not hasattr(self, 'payload_completa'):
            self.gerarPayload()
        return self.gerarQrCode(self.payload_completa)


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
                payment_amount = float(gift.price)
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
                payment_amount = float(gift.price)
            else:
                payment_amount = float(amount)
            
            # Obter informações do token para pegar payment_method_id e issuer_id
            token = data.get('token')
            payment_method_id = data.get('payment_method_id')
            issuer_id = data.get('issuer_id')
            
            # Se não vier payment_method_id, tentar obter do card token
            if not payment_method_id:
                try:
                    # Buscar informações do token
                    card_info = sdk.card_token().get(token)
                    if card_info and 'response' in card_info:
                        payment_method_id = card_info['response'].get('payment_method_id')
                        if not issuer_id:
                            issuer_id = card_info['response'].get('issuer_id')
                except Exception as e:
                    logger.error(f"Erro ao buscar info do token: {e}")
            
            # Validar campos obrigatórios
            if not payment_method_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Método de pagamento não identificado. Por favor, tente novamente.'
                }, status=400)
            
            payment_data = {
                "transaction_amount": payment_amount,
                "token": token,
                "description": gift.name,
                "installments": int(data.get('installments', 1)),
                "payment_method_id": payment_method_id,
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
            
            # Adicionar issuer_id apenas se existir
            if issuer_id:
                payment_data["issuer_id"] = issuer_id
            
            # Criar pagamento
            payment_response = sdk.payment().create(payment_data)
            payment = payment_response["response"]
            
            # Log para debug
            logger.debug(f"Payment response: {payment}")
            
            if 'id' not in payment:
                # Extrair mensagem de erro mais específica
                error_message = 'Erro ao processar pagamento'
                if 'message' in payment:
                    error_message = payment['message']
                elif 'cause' in payment:
                    causes = payment['cause']
                    if isinstance(causes, list) and len(causes) > 0:
                        error_message = causes[0].get('description', error_message)
                
                return JsonResponse({
                    'status': 'error',
                    'message': error_message,
                    'details': payment
                }, status=400)
            
            # Criar registro de pagamento
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
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Dados inválidos'
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'status': 'error',
                'message': f'Erro ao processar pagamento: {str(e)}'
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
                    old_status = payment.payment_status
                    new_status = payment_data['status']
                    
                    payment.payment_status = new_status
                    
                    if new_status == 'approved' and not payment.payment_date:
                        payment.payment_date = datetime.now()
                    
                    payment.save()
                    
                    # Enviar e-mail se aprovado
                    if new_status == 'approved':
                        try:
                            gift = payment.gift
                            if gift:
                                send_payment_confirmation_email(payment, gift)
                        except Exception as email_error:
                            logger.error(f"Erro ao enviar e-mail de confirmação: {str(email_error)}")
                    
                except Payment.DoesNotExist:
                    external_ref = payment_data.get('external_reference', '')
                    
                    if external_ref:
                        parts = external_ref.split('_')
                        
                        if len(parts) >= 2:
                            gift_type = parts[0]
                            gift_id = parts[1]
                            
                            try:
                                if gift_type == 'gift':
                                    gift = Gift.objects.get(id=gift_id)
                                else:
                                    gift = BridalShowerGift.objects.get(id=gift_id)
                                
                                content_type = ContentType.objects.get_for_model(gift)
                                payer_info = payment_data.get('payer', {})
                                payer_name = payer_info.get('first_name', '')
                                if payer_info.get('last_name'):
                                    payer_name += ' ' + payer_info.get('last_name', '')
                                
                                payer_email = payer_info.get('email', '')
                                
                                payment = Payment.objects.create(
                                    content_type=content_type,
                                    object_id=gift.id,
                                    payment_id=payment_id,
                                    payment_status=payment_data['status'],
                                    payer_name=payer_name or 'Nome não informado',
                                    payer_email=payer_email,
                                    amount=payment_data.get('transaction_amount', 0),
                                    payment_method=payment_data.get('payment_method_id', ''),
                                    installments=payment_data.get('installments', 1),
                                    payment_date=datetime.now() if payment_data['status'] == 'approved' else None
                                )
                                
                                # Enviar e-mail apropriado
                                if payment_data['status'] == 'approved':
                                    send_payment_confirmation_email(payment, gift)
                                elif payment_data['status'] in ['pending', 'in_process']:
                                    send_payment_pending_email(payment, gift)
                                    
                            except (Gift.DoesNotExist, BridalShowerGift.DoesNotExist) as e:
                                logger.error(f"Gift não encontrado: {str(e)}")
                            except Exception as gift_error:
                                logger.error(f"Erro ao processar gift: {str(gift_error)}")
            
            return HttpResponse(status=200)
            
        except json.JSONDecodeError:
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Erro no webhook: {str(e)}")
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


class PaymentSuccessView(TemplateView):
    """
    View para página de sucesso do pagamento
    """
    template_name = "home/payment-success.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        payment_id = self.request.GET.get('payment_id')
        external_reference = self.request.GET.get('external_reference')
        
        if payment_id:
            try:
                payment = Payment.objects.get(payment_id=payment_id)
                context['payment'] = payment
                context['gift'] = payment.gift
            except Payment.DoesNotExist:
                pass
        
        return context


class PaymentFailureView(TemplateView):
    """
    View para página de falha do pagamento
    """
    template_name = "home/payment-failure.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        error_raw = self.request.GET.get('error', '')
        
        if error_raw:
            print("Status Detail:j", error_raw)
            context['error_message'] = get_friendly_payment_message(error_raw, 'rejected')
            context['suggestion'] = get_payment_suggestion(error_raw)
        else:
            context['error_message'] = error_raw if error_raw else 'Não foi possível processar o pagamento.'
            context['suggestion'] = 'Verifique os dados do cartão ou tente com outro método de pagamento.'
        
        return context


class PaymentPendingView(TemplateView):
    """
    View para página de pagamento pendente
    """
    template_name = "home/payment-pending.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        payment_id = self.request.GET.get('payment_id')
        
        if payment_id:
            try:
                payment = Payment.objects.get(payment_id=payment_id)
                context['payment'] = payment
                context['gift'] = payment.gift
            except Payment.DoesNotExist:
                pass
        
        return context
