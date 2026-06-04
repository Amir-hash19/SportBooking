from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import Profile, UserAccount

SUPER_ADMIN_GROUP = "SuperAdmin"


@receiver(m2m_changed, sender=UserAccount.groups.through)
def sync_superuser_status(sender, instance, action, **kwargs):
    """
        Syncs is_superuser flag when user's groups change.
        Grants superuser if added to SuperAdmin group, revokes it if removed.
    """
    if action not in ["post_add", "post_remove", "post_clear"]:
        return

    is_super_admin = instance.groups.filter(name=SUPER_ADMIN_GROUP).exists()

    if instance.is_superuser != is_super_admin:
        instance.is_superuser = is_super_admin
        instance.save()


@receiver(post_save, sender=UserAccount, dispatch_uid="create_user_profile_unique_id")
def create_user_profile(sender, instance, created, **kwargs):
    """
        Automatically creates a Profile for every newly registered user.
        Uses get_or_create to prevent duplicate profiles on repeated signals.
    """
    if created:
        Profile.objects.get_or_create(user=instance)
