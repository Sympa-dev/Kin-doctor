from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.mail import send_mail
from .managers import UserManager
from collections.abc import Iterable

# Create your models here.

class User(AbstractUser):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True, null=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True, null=True)
    email = models.EmailField(_("email address"), blank=True, null=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    # Informations supplémentaires
    phone_number = models.CharField(
        _("numéro de téléphone"),
        max_length=20,
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(
        _("date de naissance"),
        blank=True,
        null=True
    )

    address = models.TextField(
        _("adresse"),
        blank=True,
        null=True
    )

    profile_picture = models.ImageField(
        _("photo de profil"),
        upload_to='profile_pictures/%Y/%m/',
        blank=True,
        null=True
    )

    # Champs spécifiques aux médecins
    speciality = models.CharField(
        _("spécialité"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Spécialité du médecin (si applicable)")
    )

    license_number = models.CharField(
        _("numéro de licence"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Numéro de licence médicale (si médecin)")
    )

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
    ]

    gender = models.CharField(
        _("gender"),
        max_length=10,
        choices=GENDER_CHOICES,
        default="male",
        blank=True,
        null=True,
        help_text=_(
            "Designates the gender of the user."
        ),
    )

    must_change_password = models.BooleanField(
        _("must change password"),
        default=False,
        help_text=_(
            "Designates whether this user must change their password at next login."
        ),
    )

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        abstract = False

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def has_perms(self, perm_list, obj=None):
        """
        Return True if the user has each of the specified permissions. If
        object is passed, check if the user has all required perms for it.
        """
        if not isinstance(perm_list, Iterable) or isinstance(perm_list, str):
            raise ValueError("perm_list must be an iterable of permissions.")
        return all(self.has_perm(perm, obj) for perm in perm_list)
