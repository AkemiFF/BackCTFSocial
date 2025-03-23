from django.contrib import admin

from ctf.models import *

# Register your models here.
admin.site.register(UserChallengeInstance)
admin.site.register(Challenge)
admin.site.register(ChallengeType)
admin.site.register(SSHKey)