# Django Applications

1. **accounts**
    1. User model (extending Django's AbstractUser)
    2. Authentication views
    3. Profile management
    4. User roles and permissions
    5. Models: User, UserProfile, UserSession

2. **learning**
    1. Course management
    2. Learning paths
    3. Modules and lessons
    4. Quizzes and questions
    5. Models: Course, LearningPath, Module, Quiz, Question

3. **challenges**
    1. Challenge creation and management
    2. Flag submission and verification
    3. Difficulty levels
    4. Categories
    5. Models: Challenge, Submission, Hint, Resource

4. **social**
    1. Posts and comments
    2. Social interactions (likes, shares)
    3. Following/followers
    4. Models: Post, Comment, SocialInteraction

5. **messaging**
    1. Private messaging
    2. Conversations
    3. Models: Conversation, Message

6. **teams**
    1. Team creation and management
    2. Team invitations
    3. Team challenges
    4. Models: Team, TeamMembership, TeamInvitation

7. **gamification**
    1. Points and scoring
    2. Badges and achievements
    3. Leaderboards
    4. Models: Score, Badge, Achievement, Leaderboard

8. **events**
    1. Event creation and management
    2. Event registration
    3. CTF events, workshops
    4. Models: Event, CTFEvent, Workshop, EventRegistration

9. **notifications**
    1. Notification system
    2. Email notifications
    3. In-app notifications
    4. Models: Notification

10. **api**
    1. REST API endpoints
    2. API authentication
    3. Documentation

11. **core**
    1. Shared functionality
    2. Base models
    3. Utilities
    4. Models: BaseEntity, Tag, Category
