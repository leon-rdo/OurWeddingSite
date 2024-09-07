from django.db import models
from django.forms import ValidationError


class Settings(models.Model):
    """
    Modelo para armazenar as configurações do site. 
    Este é um modelo Singleton, o que significa que só pode haver uma instância dele.
    """
    # Wedding Information
    couple_names = models.CharField("Nome do Casal", max_length=50)
    wedding_datetime = models.DateTimeField("Data do Casamento")
    ceremony_address = models.CharField("Endereço da Cerimônia", max_length=255)
    reception_address = models.CharField("Endereço da Recepção", max_length=255)
    ceremony_time = models.TimeField("Horário da Cerimônia")
    reception_time = models.TimeField("Horário da Recepção")

    # Bank Information
    bank_name = models.CharField("Nome do Banco", max_length=50, blank=True, null=True)
    pix_key = models.CharField("Chave PIX", max_length=255, blank=True, null=True)
    pix_type = models.CharField("Tipo de Chave PIX", max_length=50, choices=[('CPF', 'CPF'), ('CNPJ', 'CNPJ'), ('E-mail', 'E-mail'), ('Telefone', 'Telefone')], blank=True, null=True)
    account_holder = models.CharField("Titular da Conta", max_length=50, blank=True, null=True)

    # Website Information
    logo = models.ImageField("Logo", upload_to='home/logo/', blank=True, null=True)
    primary_color = models.CharField("Cor Primária", max_length=7, blank=True, null=True)
    secondary_color = models.CharField("Cor Secundária", max_length=7, blank=True, null=True)
    terciary_color = models.CharField("Cor Terciária", max_length=7, blank=True, null=True)

    def save(self, *args, **kwargs):
        if Settings.objects.exists() and not self.pk:
            raise ValidationError('Já existe uma instância de configurações. Edite a instância existente.')
        return super(Settings, self).save(*args, **kwargs)

    def __str__(self):
        return self.couple_names
    
    class Meta:
        verbose_name = 'Configuração do Site'
        verbose_name_plural = 'Configurações do Site'


class TextContent(models.Model):
    POSITION_CHOICES = [
        ('intro', 'Introdução'),      
        ('text_1', 'Primeiro Texto'),
        ('text_2', 'Segundo Texto'),
        ('text_3', 'Terceiro Texto'),
        ('text_4', 'Quarto Texto'),
        ('text_5', 'Quinto Texto'),
        ('leave_a_message_text', 'Texto da Mensagem'),
        ('leave_a_message_text2', 'Texto 2 da Mensagem'),
        ('last_text', 'Último Texto'),
        ('about_us_text_1', 'Texto 1 Sobre Nós'),
        ('about_us_text_2', 'Texto 2 Sobre Nós'),
        ('about_us_text_3', 'Texto 3 Sobre Nós'),
        ('about_us_text_4', 'Texto 4 Sobre Nós'),
        ('about_us_text_5', 'Texto 5 Sobre Nós'),
        ('gallery_text_1', 'Texto1 da Galeria'),
        ('gallery_text_2', 'Texto2 da Galeria'),
    ]
    
    position = models.CharField("Posição no Site", max_length=50, choices=POSITION_CHOICES)
    title = models.CharField("Título", max_length=255)
    subtitle = models.CharField("Subtítulo", max_length=255, blank=True, null=True)
    content = models.TextField("Conteúdo", blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_position_display()}: {self.title or 'Sem título'}"
    
    class Meta():
        verbose_name = 'Conteúdo de Texto'
        verbose_name_plural = 'Conteúdos de Texto'


class Gallery(models.Model):
    title = models.CharField("Título", max_length=255)
    image = models.ImageField("Imagem", upload_to='home/gallery/')
    description = models.TextField("Descrição", blank=True, null=True)
    featured = models.BooleanField("Destaque", default=False)
    position = models.CharField("Posição", max_length=10, choices=[('circles', 'Círculos'), ('gallery', 'Galeria')], blank=True, null=True)

    text_content = models.ForeignKey(TextContent, verbose_name="Conteúdo de Texto", related_name="images", on_delete=models.SET_NULL, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.featured:
            self.position = None
    
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Galeria'
        verbose_name_plural = 'Imagens'


class Guest(models.Model):
    name = models.CharField("Nome", max_length=50)
    phone = models.CharField("Telefone", max_length=20)
    will_go = models.BooleanField("Confirmado", blank=True, null=True)
    self_created = models.BooleanField("Criado pelo Usuário", default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Convidado'
        verbose_name_plural = 'Convidados'


class Message(models.Model):
    name = models.CharField("Nome", max_length=50)
    message = models.TextField("Mensagem")
    created_at = models.DateTimeField("Data de Criação", auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'


class Gift(models.Model):
    name = models.CharField("Nome", max_length=50)
    description = models.TextField("Descrição")
    image = models.ImageField("Imagem", upload_to='home/gifts/')
    price = models.DecimalField("Preço", max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Presente'
        verbose_name_plural = 'Presentes'