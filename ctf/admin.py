from django.contrib import admin

from .models import (Challenge, ChallengeCategory, ChallengeSubmission,
                     ChallengeType, DockerConfigTemplate, SSHKey,
                     UserChallengeInstance)


@admin.register(ChallengeType)
class ChallengeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'validation_type', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')

@admin.register(DockerConfigTemplate)
class DockerConfigTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'challenge_type')
    list_filter = ('challenge_type',)
    search_fields = ('challenge_type__name',)

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'challenge_type', 'difficulty', 'points', 'is_active')
    list_filter = ('challenge_type', 'difficulty', 'is_active')
    search_fields = ('title', 'description')
    readonly_fields = ('id', 'created_at', 'built_image')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'challenge_type', 'difficulty', 'description', 'points', 'is_active')
        }),
        ('Docker Configuration', {
            'fields': ('docker_image', 'docker_ports', 'environment_vars', 'startup_command', 'dockerfile', 'docker_context', 'built_image', 'setup_ssh')
        }),
        ('Flag Configuration', {
            'fields': ('static_flag', 'flag_generation_script', 'validation_script')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

@admin.register(UserChallengeInstance)
class UserChallengeInstanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'status', 'start_time', 'expiry_time')
    list_filter = ('status', 'challenge__challenge_type')
    search_fields = ('user__username', 'challenge__title')
    readonly_fields = ('container_id', 'assigned_ports', 'ssh_credentials', 'web_url', 'start_time', 'expiry_time', 'unique_flag')

@admin.register(ChallengeSubmission)
class ChallengeSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'is_correct', 'submission_time')
    list_filter = ('is_correct', 'challenge__challenge_type')
    search_fields = ('user__username', 'challenge__title', 'submitted_flag')
    readonly_fields = ('submission_time', 'logs')

@admin.register(SSHKey)
class SSHKeyAdmin(admin.ModelAdmin):
    list_display = ('user_instance', 'created_at')
    readonly_fields = ('private_key', 'public_key', 'created_at')

@admin.register(ChallengeCategory)
class ChallengeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    filter_horizontal = ('challenges',)

