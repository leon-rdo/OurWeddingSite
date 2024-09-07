from django.views.generic import TemplateView
from home.models import TextContent, Gallery


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
        print(context["featured_circles"])
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


class GalleryView(TemplateView):
    template_name = "home/gallery.html"

    def get_context_data(self, **kwargs):
        context = super(GalleryView, self).get_context_data(**kwargs)
        context["gallery_text_1"] = TextContent.objects.filter(position="gallery_text_1").first()
        context["gallery_text_2"] = TextContent.objects.filter(position="gallery_text_2").first()
        context["gallery"] = Gallery.objects.all()
        return context