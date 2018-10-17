from django.conf import settings
from django.db.models import Q
from django.db import models
from imagetagger.users.models import Team
from datetime import date


class Message(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=False)
    creation_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    expire_time = models.DateTimeField()
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_messages')

    def __str__(self):
        return u'Message: {0}'.format(str(self.title))

    @staticmethod
    def in_range(message):
        today = date.today()
        return message.filter(expire_time__gt=today, start_time__lte=today)


class TeamMessage(Message):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='message',
    )
    admins_only = models.BooleanField(default=False)

    @staticmethod
    def get_messages_for_user(user):
        userteams = Team.objects.filter(members=user)
        adminteams = Team.objects.filter(memberships__user=user, memberships__is_admin=True)
        return TeamMessage.objects.filter(Q(team__in=adminteams, admins_only=True) | Q(team__in=userteams, admins_only=False)).order_by('-start_time')


class GlobalMessage(Message):
    team_admins_only = models.BooleanField(default=False)
    staff_only = models.BooleanField(default=False)

    @staticmethod
    def get(user):
        is_admin = Team.objects.filter(memberships__user=user, memberships__is_admin=True).exists()
        is_staff = user.is_staff
        return GlobalMessage.objects.filter(
            Q(team_admins_only=False) | Q(team_admins_only=is_admin), Q(staff_only=False) | Q(staff_only=is_staff)
        ).order_by('-start_time')
