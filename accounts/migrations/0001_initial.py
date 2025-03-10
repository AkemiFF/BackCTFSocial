# Generated by Django 5.1.7 on 2025-03-10 18:04

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(blank=True, max_length=100, verbose_name='display name')),
                ('location', models.CharField(blank=True, max_length=100, verbose_name='location')),
                ('experience_level', models.CharField(blank=True, max_length=20, verbose_name='experience level')),
                ('job_title', models.CharField(blank=True, max_length=100, verbose_name='job title')),
                ('company', models.CharField(blank=True, max_length=100, verbose_name='company')),
                ('show_email', models.BooleanField(default=False, verbose_name='show email')),
                ('show_points', models.BooleanField(default=True, verbose_name='show points')),
            ],
            options={
                'verbose_name': 'user profile',
                'verbose_name_plural': 'user profiles',
            },
        ),
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(max_length=40, verbose_name='session key')),
                ('ip_address', models.GenericIPAddressField(verbose_name='IP address')),
                ('user_agent', models.TextField(verbose_name='user agent')),
                ('device_type', models.CharField(max_length=20, verbose_name='device type')),
                ('location', models.CharField(blank=True, max_length=100, verbose_name='location')),
                ('started_at', models.DateTimeField(auto_now_add=True, verbose_name='started at')),
                ('last_activity', models.DateTimeField(auto_now=True, verbose_name='last activity')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
            ],
            options={
                'verbose_name': 'user session',
                'verbose_name_plural': 'user sessions',
                'ordering': ['-last_activity'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('username', models.CharField(max_length=150, unique=True, verbose_name='username')),
                ('bio', models.TextField(blank=True, verbose_name='biography')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='profile_photos/', verbose_name='profile photo')),
                ('points', models.PositiveIntegerField(default=0, verbose_name='points')),
                ('role', models.CharField(choices=[('student', 'Student'), ('mentor', 'Mentor'), ('administrator', 'Administrator'), ('moderator', 'Moderator')], default='student', max_length=20, verbose_name='role')),
                ('is_verified', models.BooleanField(default=False, verbose_name='email verified')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('last_active', models.DateTimeField(blank=True, null=True, verbose_name='last active')),
                ('github_url', models.URLField(blank=True, verbose_name='GitHub URL')),
                ('linkedin_url', models.URLField(blank=True, verbose_name='LinkedIn URL')),
                ('twitter_url', models.URLField(blank=True, verbose_name='Twitter URL')),
                ('website_url', models.URLField(blank=True, verbose_name='Website URL')),
                ('two_factor_enabled', models.BooleanField(default=False, verbose_name='two-factor authentication')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'ordering': ['-date_joined'],
            },
        ),
        migrations.CreateModel(
            name='UserFollowing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('following_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'user following',
                'verbose_name_plural': 'user followings',
                'ordering': ['-created_at'],
            },
        ),
    ]
