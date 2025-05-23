# Generated by Django 5.0.4 on 2025-03-22 14:32

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='title')),
                ('description', models.TextField(verbose_name='description')),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard'), ('expert', 'Expert')], max_length=20, verbose_name='difficulty')),
                ('points', models.PositiveIntegerField(verbose_name='points')),
                ('flag', models.CharField(max_length=255, verbose_name='flag')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')], default='draft', max_length=20, verbose_name='status')),
                ('is_featured', models.BooleanField(default=False, verbose_name='is featured')),
                ('requires_subscription', models.BooleanField(default=False, verbose_name='requires subscription')),
                ('max_attempts', models.PositiveIntegerField(blank=True, null=True, verbose_name='maximum attempts')),
                ('time_limit_minutes', models.PositiveIntegerField(blank=True, null=True, verbose_name='time limit (minutes)')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='challenges', to='core.category')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_challenges', to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(blank=True, related_name='challenges', to='accounts.tag')),
            ],
            options={
                'verbose_name': 'challenge',
                'verbose_name_plural': 'challenges',
                'ordering': ['difficulty', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Hint',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField(verbose_name='content')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='order')),
                ('cost', models.PositiveIntegerField(default=0, help_text='Cost in points to unlock this hint', verbose_name='cost')),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hints', to='challenges.challenge')),
            ],
            options={
                'verbose_name': 'hint',
                'verbose_name_plural': 'hints',
                'ordering': ['challenge', 'order'],
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('resource_type', models.CharField(choices=[('file', 'File'), ('link', 'Link'), ('docker', 'Docker Container'), ('vm', 'Virtual Machine')], max_length=20, verbose_name='resource type')),
                ('file', models.FileField(blank=True, null=True, upload_to='challenge_resources/', verbose_name='file')),
                ('url', models.URLField(blank=True, verbose_name='URL')),
                ('docker_image', models.CharField(blank=True, max_length=255, verbose_name='docker image')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='challenges.challenge')),
            ],
            options={
                'verbose_name': 'resource',
                'verbose_name_plural': 'resources',
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('submitted_flag', models.CharField(max_length=255, verbose_name='submitted flag')),
                ('is_correct', models.BooleanField(verbose_name='is correct')),
                ('submission_time', models.DateTimeField(auto_now_add=True, verbose_name='submission time')),
                ('points_awarded', models.PositiveIntegerField(default=0, verbose_name='points awarded')),
                ('attempt_number', models.PositiveIntegerField(default=1, verbose_name='attempt number')),
                ('time_spent_seconds', models.PositiveIntegerField(default=0, verbose_name='time spent (seconds)')),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='challenges.challenge')),
                ('hints_used', models.ManyToManyField(blank=True, related_name='used_in_submissions', to='challenges.hint')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'submission',
                'verbose_name_plural': 'submissions',
                'ordering': ['-submission_time'],
            },
        ),
        migrations.CreateModel(
            name='ChallengeCompletion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_at', models.DateTimeField(auto_now_add=True, verbose_name='completed at')),
                ('points_earned', models.PositiveIntegerField(verbose_name='points earned')),
                ('time_spent_seconds', models.PositiveIntegerField(default=0, verbose_name='time spent (seconds)')),
                ('attempts', models.PositiveIntegerField(default=1, verbose_name='attempts')),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completions', to='challenges.challenge')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completed_challenges', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'challenge completion',
                'verbose_name_plural': 'challenge completions',
                'unique_together': {('user', 'challenge')},
            },
        ),
        migrations.CreateModel(
            name='ChallengeRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='rating')),
                ('feedback', models.TextField(blank=True, verbose_name='feedback')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='challenges.challenge')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='challenge_ratings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'challenge rating',
                'verbose_name_plural': 'challenge ratings',
                'unique_together': {('user', 'challenge')},
            },
        ),
        migrations.CreateModel(
            name='UserHint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unlocked_at', models.DateTimeField(auto_now_add=True, verbose_name='unlocked at')),
                ('points_deducted', models.PositiveIntegerField(default=0, verbose_name='points deducted')),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_hints', to='challenges.challenge')),
                ('hint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocked_by_users', to='challenges.hint')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocked_hints', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'user hint',
                'verbose_name_plural': 'user hints',
                'unique_together': {('user', 'hint')},
            },
        ),
    ]
