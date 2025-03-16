from accounts.models import *
from django.contrib import admin

admin.site.register(User)
admin.site.register(UserFollowing)
admin.site.register(RegistrationRequest)
admin.site.register(UserProfile)
admin.site.register(UserProjects)