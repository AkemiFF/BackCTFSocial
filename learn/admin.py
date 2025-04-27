from django.contrib import admin

from .models import (Certification, ContentItem, Course, CourseTag,
                     FileContent, ImageContent, LinkContent, Module,
                     ModuleCompletion, PointsTransaction, QuizAnswer,
                     QuizAttempt, QuizOption, QuizQuestion, Tag, TextContent,
                     UserProgress, VideoContent)

admin.site.register(CourseTag)

class CourseTagInline(admin.TabularInline):
    model = CourseTag
    extra = 1

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'category', 'instructor', 'students', 'rating')
    list_filter = ('level', 'category')
    search_fields = ('title', 'description', 'instructor')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CourseTagInline, ModuleInline]

class ContentItemInline(admin.TabularInline):
    model = ContentItem
    extra = 1

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'duration', 'order', 'points')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    inlines = [ContentItemInline]

class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    extra = 2

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'module', 'type', 'order')
    list_filter = ('module', 'type')
    search_fields = ('question', 'module__title')
    inlines = [QuizOptionInline]

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress', 'last_activity')
    list_filter = ('course',)
    search_fields = ('user__username', 'course__title')

@admin.register(ModuleCompletion)
class ModuleCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'completed_at', 'time_spent')
    list_filter = ('module__course',)
    search_fields = ('user__username', 'module__title')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'score', 'total_questions', 'time_spent', 'completed_at')
    list_filter = ('module__course',)
    search_fields = ('user__username', 'module__title')

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'certificate_id', 'issued_at')
    list_filter = ('course',)
    search_fields = ('user__username', 'course__title', 'certificate_id')

@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'transaction_type', 'description', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('user__username', 'description')

# Enregistrer les autres modèles
admin.site.register(Tag)
admin.site.register(TextContent)
admin.site.register(ImageContent)
admin.site.register(VideoContent)
admin.site.register(FileContent)
admin.site.register(LinkContent)
admin.site.register(QuizAnswer)