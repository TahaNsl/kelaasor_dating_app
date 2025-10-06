from rest_framework import permissions
from matching.models import Interaction


class NotBlockedPermission(permissions.BasePermission):
    """
    اجازه تعامل فقط وقتی که هیچکدام از دو طرف دیگری را بلاک نکرده باشد.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # فرض می‌کنیم id کاربر هدف از request.data یا kwargs گرفته میشه
        to_user_id = request.data.get("to_user") or view.kwargs.get("user_id")
        if not to_user_id:
            return False

        try:
            to_user_id = int(to_user_id)
        except ValueError:
            return False

        if Interaction.objects.filter(
            from_user=to_user_id, to_user=request.user, action=Interaction.BLOCK
        ).exists() or Interaction.objects.filter(
            from_user=request.user, to_user=to_user_id, action=Interaction.BLOCK
        ).exists():
            return False

        return True