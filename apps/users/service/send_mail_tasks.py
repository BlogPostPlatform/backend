# flake8: noqa
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)
TTL_SECONDS = settings.TTL_SECONDS
TTL_MINUTES = TTL_SECONDS // 60
# Brand Colors (extracted from website)
BRAND_COLORS = {
    "cream_bg": "#F5F1ED",
    "warm_white": "#FFFFFF",
    "primary_brown": "#3D2817",
    "accent_brown": "#7B5B3A",
    "light_brown": "#E8DDD3",
    "soft_beige": "#DFD3C7",
    "text_dark": "#4A3428",
    "text_muted": "#8B7355",
}


def get_email_base_template(title, content, footer_text=None):
    """
    Base template for all emails with unified brand design
    """
    footer = footer_text or "Agar bu xabarni siz so'ramagan bo'lsangiz, e'tibor bermang."

    return f"""<!doctype html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:{BRAND_COLORS['cream_bg']};font-family:'Georgia',serif;">
    <div style="max-width:600px;margin:40px auto;padding:0 20px;">
        <!-- Brand Header -->
        <div style="text-align:center;margin-bottom:32px;">
            <div style="display:inline-block;">
                <h1 style="font-family:'Brush Script MT','Lucida Handwriting',cursive;font-size:32px;color:{BRAND_COLORS['primary_brown']};margin:0;font-weight:400;letter-spacing:1px;">
                    Ҳафизахон Ҳайитметова
                </h1>
                <p style="font-size:11px;color:{BRAND_COLORS['text_muted']};margin:4px 0 0;letter-spacing:3px;text-transform:uppercase;">
                    Kitoblar va maqolalar
                </p>
            </div>
        </div>

        <!-- Main Card -->
        <div style="background:{BRAND_COLORS['warm_white']};border-radius:8px;overflow:hidden;box-shadow:0 4px 16px rgba(61,40,23,0.08);">
            <!-- Content Header -->
            <div style="background:linear-gradient(135deg, {BRAND_COLORS['light_brown']}, {BRAND_COLORS['soft_beige']});padding:32px 40px;border-bottom:3px solid {BRAND_COLORS['accent_brown']};">
                <h2 style="color:{BRAND_COLORS['primary_brown']};margin:0;font-size:24px;font-weight:600;text-align:center;">
                    {title}
                </h2>
            </div>

            <!-- Main Content -->
            <div style="padding:40px;">
                {content}
            </div>

            <!-- Footer -->
            <div style="background:{BRAND_COLORS['cream_bg']};padding:24px 40px;border-top:1px solid {BRAND_COLORS['soft_beige']};">
                <p style="margin:0 0 12px;font-size:13px;line-height:1.6;color:{BRAND_COLORS['text_muted']};text-align:center;">
                    {footer}
                </p>
                <p style="margin:0;font-size:12px;color:{BRAND_COLORS['text_muted']};text-align:center;">
                    Yordam kerakmi? <a href="mailto:support@hafizaxon-hayitmetova.uz" style="color:{BRAND_COLORS['accent_brown']};text-decoration:none;font-weight:500;">Qo'llab-quvvatlash xizmati</a>
                </p>
            </div>
        </div>

        <!-- Bottom Footer -->
        <div style="text-align:center;margin-top:24px;padding:0 20px;">
            <p style="margin:0 0 8px;font-size:12px;color:{BRAND_COLORS['text_muted']};">
                Muҳabbat bilan,<br>
                <strong style="color:{BRAND_COLORS['primary_brown']};">Ҳафизахон Ҳайитметова jamoasi</strong>
            </p>
            <a href="https://hafizaxon-hayitmetova.uz/" style="display:inline-block;margin-top:12px;font-size:12px;color:{BRAND_COLORS['accent_brown']};text-decoration:none;">
                hafizaxon-hayitmetova.uz
            </a>
        </div>
    </div>
</body>
</html>"""


@shared_task(bind=True, max_retries=3)
def send_email_verification_task(self, receiver_email, first_name, code):
    """
    Celery task to send email verification with unified brand design
    """
    try:
        subject = "E-mail manzilingizni tasdiqlang"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [receiver_email]

        text_content = f"""
Assalomu alaykum {first_name},

Ro'yxatdan o'tganingiz uchun rahmat! Hisobingizni himoya qilish uchun e-mail manzilingizni tasdiqlang.

Sizning 4 raqamli tasdiqlash kodingiz: {code}

Tasdiqlash jarayonini yakunlash uchun ushbu kodni veb-saytimizda kiriting.

Agar buni siz so'ramagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring.

Muҳabbat bilan,
Ҳафизахон Ҳайитметова jamoasi
        """

        content = f"""
            <p style="margin:0 0 16px;font-size:16px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Assalomu alaykum <strong style="color:{BRAND_COLORS['primary_brown']};">{first_name}</strong>,
            </p>
            <p style="margin:0 0 24px;font-size:15px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Ro'yxatdan o'tganingiz uchun rahmat! Hisobingizni himoya qilish uchun
                e-mail manzilingizni tasdiqlang.
            </p>

            <!-- Code Display -->
            <div style="background:{BRAND_COLORS['cream_bg']};border:2px solid {BRAND_COLORS['accent_brown']};border-radius:12px;padding:28px;margin:32px 0;text-align:center;">
                <p style="margin:0 0 12px;font-size:14px;color:{BRAND_COLORS['text_muted']};text-transform:uppercase;letter-spacing:2px;">
                    Tasdiqlash kodi
                </p>
                <div style="font-family:'Courier New',monospace;font-size:40px;font-weight:700;color:{BRAND_COLORS['primary_brown']};letter-spacing:8px;">
                    {code}
                </div>
            </div>

            <p style="margin:0;font-size:14px;line-height:1.7;color:{BRAND_COLORS['text_dark']};text-align:center;">
                Tasdiqlash jarayonini yakunlash uchun ushbu kodni veb-saytimizda kiriting.
            </p>
        """

        html_content = get_email_base_template("E-mail tasdiqlash", content)

        email = EmailMultiAlternatives(subject, text_content, from_email, to)
        email.attach_alternative(html_content, "text/html")
        email.send()

        logger.info(f"Email verification sent successfully to {receiver_email}")
        return f"Email sent to {receiver_email}"

    except Exception as exc:
        logger.error(f"Failed to send email verification to {receiver_email}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_password_verification_task(self, email, first_name, code):
    """
    Celery task to send password reset verification with unified brand design
    """
    try:
        subject = "Parolni tiklash so'rovi"
        to = [email]
        from_email = settings.DEFAULT_FROM_EMAIL

        text_content = f"""
Assalomu alaykum {first_name},

Hisobingiz parolini tiklash so'rovini oldik.

Sizning 4 raqamli parol tiklash kodingiz: {code}

Yangi parol o'rnatish uchun ushbu kodni veb-saytimizda kiriting.

Agar parolni tiklashni siz so'ramagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring.

Muҳabbat bilan,
Ҳафизахон Ҳайитметова jamoasi
        """

        content = f"""
            <p style="margin:0 0 16px;font-size:16px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Assalomu alaykum <strong style="color:{BRAND_COLORS['primary_brown']};">{first_name}</strong>,
            </p>
            <p style="margin:0 0 24px;font-size:15px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Hisobingiz parolini tiklash so'rovini oldik. Xavfsizligingiz uchun,
                ushbu kodni faqat siz bilishingiz kerak.
            </p>

            <!-- Code Display -->
            <div style="background:{BRAND_COLORS['cream_bg']};border:2px solid {BRAND_COLORS['accent_brown']};border-radius:12px;padding:28px;margin:32px 0;text-align:center;">
                <p style="margin:0 0 12px;font-size:14px;color:{BRAND_COLORS['text_muted']};text-transform:uppercase;letter-spacing:2px;">
                    Parol tiklash kodi
                </p>
                <div style="font-family:'Courier New',monospace;font-size:40px;font-weight:700;color:{BRAND_COLORS['primary_brown']};letter-spacing:8px;">
                    {code}
                </div>
            </div>

            <div style="background:#FFF8F0;border-left:4px solid {BRAND_COLORS['accent_brown']};padding:16px 20px;margin:24px 0;border-radius:4px;">
                <p style="margin:0;font-size:13px;line-height:1.6;color:{BRAND_COLORS['text_dark']};">
                    <strong>Xavfsizlik eslatmasi:</strong> Bu kodni hech kim bilan baham ko'rmang.
                    Kod cheklangan vaqt davomida amal qiladi.
                </p>
            </div>

            <p style="margin:0;font-size:14px;line-height:1.7;color:{BRAND_COLORS['text_dark']};text-align:center;">
                Yangi parol o'rnatish uchun ushbu kodni veb-saytimizda kiriting.
            </p>
        """

        html_content = get_email_base_template("Parolni tiklash", content)

        email_msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()

        logger.info(f"Password reset email sent successfully to {email}")
        return f"Password reset email sent to {email}"

    except Exception as exc:
        logger.error(f"Failed to send password reset email to {email}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_email_change_verification_task(self, receiver_new_email, first_name, code):
    """
    Celery task to send email change verification with unified brand design
    """
    try:
        subject = "Yangi e-mail manzilingizni tasdiqlang"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [receiver_new_email]

        text_content = f"""
Assalomu alaykum {first_name},

Hisobingiz bilan bog'langan e-mail manzilingizni o'zgartirish so'rovini oldik.

Yangi e-mailingizni tasdiqlash uchun quyidagi 4 raqamli kodni kiriting:

{code}

Agar bu o'zgarishni siz so'ramagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring.

Muҳabbat bilan,
Ҳафизахон Ҳайитметова jamoasi
        """

        content = f"""
            <p style="margin:0 0 16px;font-size:16px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Assalomu alaykum <strong style="color:{BRAND_COLORS['primary_brown']};">{first_name}</strong>,
            </p>
            <p style="margin:0 0 24px;font-size:15px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Hisobingiz bilan bog'langan e-mail manzilingizni o'zgartirish so'rovini oldik.
                Davom etish uchun quyidagi kodni kiriting.
            </p>

            <!-- Code Display -->
            <div style="background:{BRAND_COLORS['cream_bg']};border:2px solid {BRAND_COLORS['accent_brown']};border-radius:12px;padding:28px;margin:32px 0;text-align:center;">
                <p style="margin:0 0 12px;font-size:14px;color:{BRAND_COLORS['text_muted']};text-transform:uppercase;letter-spacing:2px;">
                    Tasdiqlash kodi
                </p>
                <div style="font-family:'Courier New',monospace;font-size:40px;font-weight:700;color:{BRAND_COLORS['primary_brown']};letter-spacing:8px;">
                    {code}
                </div>
            </div>

            <p style="margin:0;font-size:14px;line-height:1.7;color:{BRAND_COLORS['text_dark']};text-align:center;">
                Yangi e-mail manzilingizni tasdiqlash uchun ushbu kodni veb-saytimizda kiriting.
            </p>
        """

        html_content = get_email_base_template("E-mail o'zgartirish", content)

        email = EmailMultiAlternatives(subject, text_content, from_email, to)
        email.attach_alternative(html_content, "text/html")
        email.send()

        logger.info(f"Email change verification sent successfully to {receiver_new_email}")
        return f"Email change verification sent to {receiver_new_email}"

    except Exception as exc:
        logger.error(
            f"Failed to send email change verification to {receiver_new_email}: {str(exc)}"
        )
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_activation_invite_task(self, email, first_name, uid, token):
    """
    Celery task to send activation invite with unified brand design
    """
    try:
        subject = "Platformamizga xush kelibsiz"
        from_email = settings.DEFAULT_FROM_EMAIL
        activation_link = f"{settings.FRONTEND_URL}/activate?uid={uid}&token={token}"
        to = [email]

        text_content = f"""Assalomu alaykum {first_name},

Platformamizga qo'shilishingiz uchun taklifnoma oldingiz.

Boshlash uchun hisobingizni faollashtiring:
{activation_link}

Agar bu taklifnomani kutmagan bo'lsangiz, xabarni e'tiborsiz qoldiring.

— Ҳафизахон Ҳайитметова jamoasi
"""

        content = f"""
            <p style="margin:0 0 16px;font-size:16px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Assalomu alaykum <strong style="color:{BRAND_COLORS['primary_brown']};">{first_name}</strong>,
            </p>
            <p style="margin:0 0 28px;font-size:15px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Platformamizga qo'shilishingiz uchun taklifnoma oldingiz. Boshlash uchun
                e-mail manzilingizni tasdiqlang va hisobingizni sozlang.
            </p>

            <!-- CTA Button -->
            <div style="text-align:center;margin:36px 0;">
                <a href="{activation_link}"
                   style="display:inline-block;padding:16px 40px;background:{BRAND_COLORS['primary_brown']};color:#FFFFFF;text-decoration:none;border-radius:50px;font-size:16px;font-weight:600;letter-spacing:0.5px;box-shadow:0 4px 12px rgba(61,40,23,0.2);">
                    Hisobni faollashtirish
                </a>
            </div>

            <!-- Link Alternative -->
            <div style="background:{BRAND_COLORS['cream_bg']};padding:20px;border-radius:8px;margin:32px 0;">
                <p style="margin:0 0 8px;font-size:12px;color:{BRAND_COLORS['text_muted']};text-align:center;">
                    Yoki ushbu havolani brauzeringizga nusxalang:
                </p>
                <p style="margin:0;font-size:12px;color:{BRAND_COLORS['accent_brown']};text-align:center;word-break:break-all;line-height:1.6;">
                    <a href="{activation_link}" style="color:{BRAND_COLORS['accent_brown']};text-decoration:underline;">
                        {activation_link}
                    </a>
                </p>
            </div>
        """

        html_content = get_email_base_template(
            "Hisobni faollashtirish",
            content,
            "Agar bu taklifnomani kutmagan bo'lsangiz, xabarni e'tiborsiz qoldiring.",
        )

        email_msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()

        logger.info(f"Activation invite sent successfully to {email}")
        return f"Activation invite sent to {email}"

    except Exception as exc:
        logger.error(f"Failed to send activation invite to {email}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_otp_verification_task(self, email, first_name, otp_code):
    """
    Celery task to send 2FA OTP verification with unified brand design
    """
    try:
        subject = "Kirish tasdiqlash kodi"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [email]

        text_content = f"""Assalomu alaykum {first_name},

Sizning tasdiqlash kodingiz: {otp_code}

Kirishni yakunlash uchun ushbu kodni kiriting. Bu kod {TTL_MINUTES} daqiqa davomida amal qiladi.

Agar bu kodni siz so'ramagan bo'lsangiz, xabarni e'tiborsiz qoldiring va parolingizni o'zgartirishni o'ylab ko'ring.

— Ҳафизахон Ҳайитметова jamoasi
"""

        content = f"""
            <p style="margin:0 0 16px;font-size:16px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Assalomu alaykum <strong style="color:{BRAND_COLORS['primary_brown']};">{first_name}</strong>,
            </p>
            <p style="margin:0 0 28px;font-size:15px;line-height:1.7;color:{BRAND_COLORS['text_dark']};">
                Kirishni yakunlash uchun quyidagi tasdiqlash kodini kiriting:
            </p>

            <!-- OTP Code Display -->
            <div style="background:{BRAND_COLORS['cream_bg']};border:2px solid {BRAND_COLORS['accent_brown']};border-radius:12px;padding:32px;margin:32px 0;text-align:center;">
                <p style="margin:0 0 16px;font-size:14px;color:{BRAND_COLORS['text_muted']};text-transform:uppercase;letter-spacing:2px;">
                    Tasdiqlash kodi
                </p>
                <div style="font-family:'Courier New',monospace;font-size:48px;font-weight:700;color:{BRAND_COLORS['primary_brown']};letter-spacing:12px;line-height:1;">
                    {otp_code}
                </div>
            </div>

            <p style="margin:0 0 24px;font-size:14px;line-height:1.7;color:{BRAND_COLORS['text_dark']};text-align:center;">
                Bu kod <strong style="color:{BRAND_COLORS['primary_brown']};">{TTL_MINUTES} daqiqa</strong> davomida amal qiladi
            </p>

            <!-- Security Warning -->
            <div style="background:#FFF8F0;border-left:4px solid {BRAND_COLORS['accent_brown']};padding:16px 20px;border-radius:4px;">
                <p style="margin:0;font-size:13px;line-height:1.6;color:{BRAND_COLORS['text_dark']};">
                    <strong>Xavfsizlik maslaҳati:</strong> Bu kodni hech kim bilan baham ko'rmang.
                    Bizning jamoamiz hech qachon tasdiqlash kodini so'ramaydi.
                </p>
            </div>
        """

        html_content = get_email_base_template(
            "Kirish tasdiqlash",
            content,
            "Agar bu kodni siz so'ramagan bo'lsangiz, xabarni e'tiborsiz qoldiring.",
        )

        email_msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.extra_headers = {
            "X-Priority": "1",
            "X-MSMail-Priority": "High",
        }
        email_msg.send()

        logger.info(f"OTP verification code sent successfully to {email}")
        return f"OTP verification code sent to {email}"

    except Exception as exc:
        logger.error(f"Failed to send OTP verification code to {email}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))
