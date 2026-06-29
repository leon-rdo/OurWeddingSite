# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based wedding website called "OurWeddingSite" featuring:
- Wedding information display (ceremony, reception, bridal shower details)
- Photo gallery with featured images
- Gift registry with two types: wedding gifts and bridal shower gifts
- RSVP system for guest confirmations
- Message board for guests to leave messages
- Mercado Pago payment integration for gift contributions
- Email notifications for payment confirmations
- Admin interface customized with Jazzmin

The site is fully configurable through a singleton Settings model, allowing the couple to customize colors, hide/show sections, and manage all wedding details without code changes.

## Development Commands

> **Python version:** This project targets **Python 3.14** for local development (declared in `.python-version`). CI validates against a **3.12 + 3.14** matrix ([.github/workflows/ci.yml](.github/workflows/ci.yml)), so keep dependencies installable on both. Create the venv with `python3.14 -m venv .venv`. C-extension deps (notably Pillow) must be pinned to versions that ship wheels for the target Python — Pillow is pinned to a 3.14-compatible release in [requirements.txt](requirements.txt).

```bash
# Run dev server
python manage.py runserver

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Static files (production)
python manage.py collectstatic --noinput

# Tests (note: home/tests.py is currently empty)
python manage.py test home
python manage.py test home.tests.TestClassName

# Production
gunicorn -c configs/gunicorn.py OurWeddingSite.wsgi:application
```

## Architecture

### Core Design Patterns

**Singleton Settings Model**: The `Settings` model enforces a single instance pattern ([home/models.py:49-52](home/models.py#L49-L52)) — only one site configuration instance is allowed. All site-wide settings (colors, dates, addresses, feature toggles) come from this model.

**Generic Relations for Payments**: The `Payment` model uses Django's `GenericForeignKey` to link to either `Gift` or `BridalShowerGift` ([home/models.py:154-156](home/models.py#L154-L156)), providing a unified payment system for both gift types.

**Context Processor Pattern**: `Settings` is globally available in all templates through [OurWeddingSite/context_processors.py](OurWeddingSite/context_processors.py) — no need to pass it in every view.

**View Visibility Pattern**: Public views that can be hidden use `UserPassesTestMixin`. The `test_func` checks the relevant `Settings.hide_*` flag; if hidden, it falls back to checking a Django permission. Example: `GalleryView.test_func` returns `True` if `hide_gallery` is False, otherwise requires `home.view_gallery` permission. Apply this pattern to any new hideable section.

### App Structure

**Single App Architecture**: All functionality lives in the `home` app — public views, payment processing, webhooks, and email notifications.

### Payment Flows

There are **two distinct payment flows**:

**1. Redirect Checkout (Mercado Pago hosted page)**
1. `CreatePaymentView.post` receives gift info + buyer details, creates a Mercado Pago preference
2. Returns `preference_id` and `init_point` URL; frontend redirects user to Mercado Pago
3. After payment, Mercado Pago redirects to success/failure/pending URLs
4. Separately, Mercado Pago sends a webhook to `MercadoPagoWebhookView`
5. Webhook updates `Payment` status and sends confirmation email

**2. Transparent Checkout (card processed in-page)**
1. Frontend collects card data via Mercado Pago JS SDK and gets a card token
2. `ProcessPaymentView.post` receives the token + gift info, creates a payment directly via `sdk.payment().create()`
3. Creates a local `Payment` record immediately
4. `MercadoPagoWebhookView` receives status updates and updates the record

**PIX Payments**: The `Payload` class in [home/views.py](home/views.py) generates PIX QR codes (EMV format with CRC16). It is used inline in `GiftListView` and `BridalShowerGiftListView` to attach `qr_code` (base64 PNG) and `payload` (copy-paste string) attributes directly onto gift objects before passing to templates.

### Key Models

- **Settings**: Singleton — wedding details, bank/PIX info, colors, `hide_*` feature toggles
- **TextContent**: Text blocks placed throughout the site via a `position` choice field (e.g. `intro`, `text_1`, `gift_list_text`, `bridal_shower_text`)
- **Gallery**: Images with optional featured positioning (`circles` or `gallery`); non-featured images auto-clear `position` on save
- **Gift**: Wedding gift with price; `total_paid`, `remaining_amount`, `is_fully_paid` are computed properties
- **BridalShowerGift**: Bridal shower gift — optional price, category, `colors` (M2M → `BridalShowerGiftColor`), optional `guest_name/phone/email/way_to_gift` assignment. Unassigned gifts are shown to all; assigned gifts are filtered by guest phone/email via query params.
- **BridalShowerGiftColor**: Reusable color swatches (hex + name) for bridal shower gifts
- **BridalShowerGiftSuggestion**: Purchase links for a `BridalShowerGift` (FK → gift, name + URL)
- **Payment**: Generic payment linked to any gift type; tracks status, payer info, amount, method, installments
- **Guest**: RSVP records; guests are pre-created by admin. `self_created=True` means the guest added themselves via the site
- **Message**: Guest messages/well-wishes

### RSVP Flow

`RSVPFormView.post` uses an `action` parameter to dispatch operations:
- `check_phone` — look up guest by phone; returns single/multiple/not-found
- `confirm_name` — confirm identity when multiple guests share a phone
- `create_guest` — create a self-service guest (`self_created=True`)
- `submit_rsvp` — set `guest.will_go`

### Template Organization

- Base template: [templates/base.html](templates/base.html)
- App templates: [home/templates/home/](home/templates/home/)
- Email templates: [home/templates/home/emails/](home/templates/home/emails/)

Static files are in [static/home/](static/home/) with `css/`, `scripts/`, and `media/` subdirectories.

### Environment Configuration

The project uses python-dotenv. Required variables:
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- `MERCADO_PAGO_ACCESS_TOKEN`, `MERCADO_PAGO_PUBLIC_KEY`, `MERCADO_PAGO_WEBHOOK_URL`
- `SITE_URL` — full URL used to build webhook and back-URL callbacks
- Email: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

### Logging

Configured in [OurWeddingSite/settings.py:86-183](OurWeddingSite/settings.py#L86-L183). All logs rotate at 10 MB:
- `django.log` — general INFO logs
- `errors.log` — ERROR level only
- `payments.log` — payment operations

Logger names to use:
- `logging.getLogger("home")` — general app logs
- `logging.getLogger("payments")` — payment operations

### Database

SQLite by default ([OurWeddingSite/settings.py:192-197](OurWeddingSite/settings.py#L192-L197)), file at `db.sqlite3`. Uses `America/Belem` timezone with `USE_TZ = False` — all datetimes are naive/stored without timezone info.

### Admin Interface

Customized with django-jazzmin. Configuration at [OurWeddingSite/jazzmin.py](OurWeddingSite/jazzmin.py). All models are registered with custom admin classes in [home/admin.py](home/admin.py).

### CI/CD

GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs `migrate`, `collectstatic`, and `test` on every push/PR to `main`. On merge to `main`, it deploys via SSH: pulls code, activates virtualenv, migrates, collects static, and restarts Gunicorn.

## Important Notes

### Payment Security

- Webhook validation is critical — payment status updates must only come through `MercadoPagoWebhookView`, never from client-side redirect query params alone
- The webhook view is CSRF-exempt but always re-fetches payment data from the Mercado Pago API to verify; it never trusts the webhook payload directly

### Model Constraints

- `Settings.save()` raises `ValidationError` if a second instance is created
- `Gallery.save()` clears `position` when `featured=False`
- `Gift`/`BridalShowerGift` payment totals (`total_paid`, `remaining_amount`, `is_fully_paid`) are computed from DB aggregates on each access — avoid calling them in loops over large querysets

### Deployment

- `DEBUG=False` enables SSL redirect and secure proxy headers
- The `logs/` directory must exist and be writable before starting Gunicorn
- Gunicorn config: [configs/gunicorn.py](configs/gunicorn.py)
