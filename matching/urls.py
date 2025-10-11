from django.urls import path
from matching.views import (LikeUserView, NotificationsView,
                            RespondToLikeView, BlockUserView, UnblockUserView)

urlpatterns = [
    path("like/", LikeUserView.as_view(), name="like-user"),
    path("notifications/", NotificationsView.as_view(), name="notifications"),
    path("respond/", RespondToLikeView.as_view(), name="respond-to-like"),
    path("block/<int:user_id>/", BlockUserView.as_view(), name="block-user"),
    path("unblock/<int:user_id>/", UnblockUserView.as_view(), name="unblock-user"),
]