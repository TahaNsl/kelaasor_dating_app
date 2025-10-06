from celery import shared_task
from django.utils import timezone
from .models import Interaction, Match

@shared_task
def clean_old_interactions():
    """
    پاکسازی Interactionهای LIKE که دیگر نیازی به آنها نیست:
    - Interaction هایی که پاسخ داده شده (Match یا Pass)
    """

    likes = Interaction.objects.filter(action=Interaction.LIKE)

    deleted_count = 0
    for like in likes:
        match_exists = Match.objects.filter(
            user1__in=[like.from_user, like.to_user],
            user2__in=[like.from_user, like.to_user]
        ).exists()

        pass_exists = Interaction.objects.filter(
            from_user=like.to_user,
            to_user=like.from_user,
            action=Interaction.PASS
        ).exists()

        if match_exists or pass_exists:
            like.delete()
            deleted_count += 1

    return f"Deleted {deleted_count} old LIKE interactions."