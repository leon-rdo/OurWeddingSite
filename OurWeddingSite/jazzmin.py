JAZZMIN_SETTINGS = {
    "site_title": "Casamento",
    "site_header": "Painel do Casamento",
    "site_brand": "Wedding Bliss",
    "welcome_sign": "Bem-vindo ao Painel",

    "topmenu_links": [
        {"name": "Ver Site", "url": "home:index"},
        {"name": "Mensagens", "url": "admin:home_message_changelist"},
        {"name": "Configurações do Site", "url": "/admin/home/settings/1/change/"},
    ],

    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_models": [],

    # Ícones personalizados para os modelos
    "icons": {
        "auth.group": "fas fa-users",
        "auth.user": "fas fa-user",
        "home": "fas fa-home",
        "home.settings": "fas fa-cogs",
        "home.textcontent": "fas fa-file-alt",
        "home.gallery": "fas fa-images",
        "home.gift": "fas fa-gift",
        "home.message": "fas fa-envelope",
        "home.guest": "fas fa-users",
        "home.BridalShowerGift": "fas fa-gift",
        "home.BridalShowerGiftColor": "fas fa-paint-brush",
    },

    "changeform_format": "single",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-light",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-info",
    "sidebar_nav_small_text": True,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True
}
