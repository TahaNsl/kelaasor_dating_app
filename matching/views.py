from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from matching.models import Interaction, Match, Notification
from matching.permissions import NotBlockedPermission
from matching.serializers import InteractionSerializer, NotificationSerializer


User = get_user_model()

class LikeUserView(generics.CreateAPIView):
    serializer_class = InteractionSerializer
    permission_classes = [permissions.IsAuthenticated, NotBlockedPermission]

    def post(self, request, *args, **kwargs):
        to_user_id = request.data.get("to_user")
        if not to_user_id:
            return Response({"detail": "to_user field is required."}, status=status.HTTP_400_BAD_REQUEST)

        if to_user_id == request.user.id:
            return Response({"detail": "You cannot like yourself."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        interaction, created = Interaction.objects.get_or_create(
            from_user=request.user,
            to_user=to_user,
            defaults={"action": Interaction.LIKE},
        )

        if not created:
            return Response({"detail": "You already liked this user."}, status=status.HTTP_400_BAD_REQUEST)

        Notification.objects.create(
            user=to_user,
            message=f"{request.user.username} liked you.",
        )

        return Response({"detail": "User liked successfully."}, status=status.HTTP_201_CREATED)


class NotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.notifications.order_by("-created_at")


class RespondToLikeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from_user_id = request.data.get("from_user")
        action = request.data.get("action")  # 'like' or 'pass'

        if not from_user_id or action not in ["like", "pass"]:
            return Response({"detail": "Invalid data."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interaction = Interaction.objects.get(from_user_id=from_user_id, to_user=request.user)
        except Interaction.DoesNotExist:
            return Response({"detail": "No like found from this user."}, status=status.HTTP_404_NOT_FOUND)

        if action == "like":
            if Interaction.objects.filter(from_user=request.user, to_user=interaction.from_user, action="like").exists():
                return Response({"detail": "You already liked this user."}, status=status.HTTP_400_BAD_REQUEST)

            Interaction.objects.create(from_user=request.user, to_user=interaction.from_user, action="like")

            Match.objects.get_or_create(
                user1=min(request.user, interaction.from_user, key=lambda u: u.id),
                user2=max(request.user, interaction.from_user, key=lambda u: u.id)
            )

            Notification.objects.create(
                user=interaction.from_user,
                message=f"You matched with {request.user.username}!"
            )

            return Response({"detail": "It's a match!"}, status=status.HTTP_201_CREATED)

        elif action == "pass":
            interaction.delete()
            return Response({"detail": "You passed this user."}, status=status.HTTP_200_OK)


class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """
        Block another user:
        - ایجاد Interaction با action='block'
        - جلوگیری از duplicate
        """
        try:
            to_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user == to_user:
            return Response({"detail": "You cannot block yourself."}, status=status.HTTP_400_BAD_REQUEST)

        interaction, created = Interaction.objects.get_or_create(
            from_user=request.user,
            to_user=to_user,
            defaults={"action": Interaction.BLOCK},
        )

        if not created:
            return Response({"detail": "You already blocked this user."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": f"You blocked {to_user.username} successfully."}, status=status.HTTP_201_CREATED
        )


class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        """Unblock a previously blocked user"""
        try:
            to_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = Interaction.objects.filter(
            from_user=request.user, to_user=to_user, action=Interaction.BLOCK
        ).delete()

        if deleted:
            return Response({"detail": f"You unblocked {to_user.username}."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "You haven't blocked this user."}, status=status.HTTP_400_BAD_REQUEST)
