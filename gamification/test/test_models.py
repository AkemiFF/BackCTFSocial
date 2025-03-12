# gamification/tests/test_models.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from ..models import (Achievement, Badge, Challenge, Leaderboard,
                      LeaderboardEntry, Level, Point, Reward, UserAchievement,
                      UserBadge, UserChallenge, UserLevel, UserReward)

User = get_user_model()


class PointModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.point = Point.objects.create(
            user=self.user,
            amount=100,
            source='test',
            description='Test points'
        )
    
    def test_point_creation(self):
        self.assertEqual(self.point.user, self.user)
        self.assertEqual(self.point.amount, 100)
        self.assertEqual(self.point.source, 'test')
        self.assertEqual(self.point.description, 'Test points')
        self.assertIsNotNone(self.point.created_at)


class LevelModelTest(TestCase):
    def setUp(self):
        self.level = Level.objects.create(
            number=1,
            name='Beginner',
            points_required=0
        )
    
    def test_level_creation(self):
        self.assertEqual(self.level.number, 1)
        self.assertEqual(self.level.name, 'Beginner')
        self.assertEqual(self.level.points_required, 0)


class UserLevelModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.level1 = Level.objects.create(
            number=1,
            name='Beginner',
            points_required=0
        )
        
        self.level2 = Level.objects.create(
            number=2,
            name='Intermediate',
            points_required=100
        )
        
        self.user_level = UserLevel.objects.create(
            user=self.user,
            level=self.level1,
            total_points=0
        )
    
    def test_user_level_creation(self):
        self.assertEqual(self.user_level.user, self.user)
        self.assertEqual(self.user_level.level, self.level1)
        self.assertEqual(self.user_level.total_points, 0)
        self.assertEqual(self.user_level.points_to_next_level, 100)
    
    def test_update_level(self):
        # Add points to reach level 2
        self.user_level.total_points = 100
        self.user_level.save()
        
        # Update level
        result = self.user_level.update_level()
        
        self.assertTrue(result)
        self.assertEqual(self.user_level.level, self.level2)


class BadgeModelTest(TestCase):
    def setUp(self):
        self.badge = Badge.objects.create(
            name='Test Badge',
            description='A test badge',
            category='test',
            points_value=50
        )
    
    def test_badge_creation(self):
        self.assertEqual(self.badge.name, 'Test Badge')
        self.assertEqual(self.badge.description, 'A test badge')
        self.assertEqual(self.badge.category, 'test')
        self.assertEqual(self.badge.points_value, 50)
        self.assertFalse(self.badge.is_hidden)


class UserBadgeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.badge = Badge.objects.create(
            name='Test Badge',
            description='A test badge',
            category='test',
            points_value=50
        )
        
        self.user_badge = UserBadge.objects.create(
            user=self.user,
            badge=self.badge
        )
    
    def test_user_badge_creation(self):
        self.assertEqual(self.user_badge.user, self.user)
        self.assertEqual(self.user_badge.badge, self.badge)
        self.assertIsNotNone(self.user_badge.earned_at)


class ChallengeModelTest(TestCase):
    def setUp(self):
        self.badge = Badge.objects.create(
            name='Challenge Badge',
            description='A badge for completing a challenge',
            category='challenge',
            points_value=50
        )
        
        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            description='A test challenge',
            difficulty='medium',
            points_reward=100,
            badge_reward=self.badge,
            completion_criteria={'tasks_completed': 5}
        )
    
    def test_challenge_creation(self):
        self.assertEqual(self.challenge.title, 'Test Challenge')
        self.assertEqual(self.challenge.description, 'A test challenge')
        self.assertEqual(self.challenge.difficulty, 'medium')
        self.assertEqual(self.challenge.points_reward, 100)
        self.assertEqual(self.challenge.badge_reward, self.badge)
        self.assertEqual(self.challenge.completion_criteria, {'tasks_completed': 5})
        self.assertEqual(self.challenge.status, 'active')
        self.assertTrue(self.challenge.is_active)


class UserChallengeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.badge = Badge.objects.create(
            name='Challenge Badge',
            description='A badge for completing a challenge',
            category='challenge',
            points_value=50
        )
        
        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            description='A test challenge',
            difficulty='medium',
            points_reward=100,
            badge_reward=self.badge,
            completion_criteria={'tasks_completed': 5}
        )
        
        self.user_challenge = UserChallenge.objects.create(
            user=self.user,
            challenge=self.challenge,
            progress={'tasks_completed': 0}
        )
    
    def test_user_challenge_creation(self):
        self.assertEqual(self.user_challenge.user, self.user)
        self.assertEqual(self.user_challenge.challenge, self.challenge)
        self.assertEqual(self.user_challenge.status, 'in_progress')
        self.assertEqual(self.user_challenge.progress, {'tasks_completed': 0})
        self.assertEqual(self.user_challenge.progress_percentage, 0)
        self.assertIsNotNone(self.user_challenge.started_at)
        self.assertIsNone(self.user_challenge.completed_at)
    
    def test_update_progress(self):
        # Update progress to 60%
        progress = self.user_challenge.update_progress({'tasks_completed': 3})
        
        self.assertEqual(progress, 60)
        self.assertEqual(self.user_challenge.progress_percentage, 60)
        self.assertEqual(self.user_challenge.status, 'in_progress')
        
        # Complete the challenge
        progress = self.user_challenge.update_progress({'tasks_completed': 5})
        
        self.assertEqual(progress, 100)
        self.assertEqual(self.user_challenge.progress_percentage, 100)
        self.assertEqual(self.user_challenge.status, 'completed')
        self.assertIsNotNone(self.user_challenge.completed_at)


# Add more tests for other models as needed