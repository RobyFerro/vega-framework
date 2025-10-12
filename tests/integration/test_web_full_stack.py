"""Integration tests for full-stack Vega Web application"""

import pytest
from starlette.testclient import TestClient
from vega.web import VegaApp, Router, Request, HTTPException, status
from vega.di import Container, injectable
from vega.events import EventBus, Event, subscribe


# Domain Events
class UserRegisteredEvent(Event):
    """Event fired when a user registers"""
    def __init__(self, user_id: str, email: str):
        super().__init__()
        self.user_id = user_id
        self.email = email


# Services
@injectable()
class UserService:
    """User service with event publishing"""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.users = {}

    async def register_user(self, email: str) -> dict:
        """Register a new user and publish event"""
        user_id = f"user_{len(self.users) + 1}"
        user = {"id": user_id, "email": email}
        self.users[user_id] = user

        # Publish event
        await self.event_bus.publish(UserRegisteredEvent(user_id, email))

        return user

    def get_user(self, user_id: str) -> dict:
        """Get user by ID"""
        if user_id not in self.users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return self.users[user_id]


# Event Handlers
@injectable()
class WelcomeEmailHandler:
    """Handler that sends welcome emails"""
    def __init__(self):
        self.sent_emails = []

    @subscribe(UserRegisteredEvent)
    async def handle(self, event: UserRegisteredEvent):
        """Send welcome email on user registration"""
        # Simulate sending email
        self.sent_emails.append({
            "to": event.email,
            "subject": "Welcome!",
            "user_id": event.user_id
        })


@pytest.fixture
def app():
    """Create full-stack test application"""
    # Setup DI container
    container = Container()
    event_bus = EventBus()

    # Register services
    container.register_singleton(EventBus, event_bus)
    container.register(UserService)
    container.register(WelcomeEmailHandler)

    # Register event handlers
    email_handler = container.resolve(WelcomeEmailHandler)
    event_bus.register(email_handler.handle)

    # Create app
    app = VegaApp(
        title="Integration Test App",
        version="1.0.0",
        debug=True
    )

    # Store references for testing
    app.state.container = container
    app.state.event_bus = event_bus
    app.state.email_handler = email_handler

    # Setup routes
    router = Router(prefix="/api")

    @router.post("/users/register")
    async def register_user(request: Request):
        """Register new user endpoint"""
        data = await request.json()
        user_service = container.resolve(UserService)
        user = await user_service.register_user(data["email"])
        return user

    @router.get("/users/{user_id}")
    async def get_user(user_id: str):
        """Get user endpoint"""
        user_service = container.resolve(UserService)
        return user_service.get_user(user_id)

    app.include_router(router)

    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestFullStackIntegration:
    """Test complete application workflow"""

    @pytest.mark.asyncio
    async def test_user_registration_workflow(self, app, client):
        """Test complete user registration workflow with events"""
        # Register a new user
        response = client.post(
            "/api/users/register",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        user_data = response.json()
        assert "id" in user_data
        assert user_data["email"] == "test@example.com"

        # Verify user can be retrieved
        user_id = user_data["id"]
        response = client.get(f"/api/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

        # Verify welcome email was sent
        email_handler = app.state.email_handler
        assert len(email_handler.sent_emails) == 1
        email = email_handler.sent_emails[0]
        assert email["to"] == "test@example.com"
        assert email["subject"] == "Welcome!"
        assert email["user_id"] == user_id

    def test_user_not_found(self, client):
        """Test error handling for non-existent user"""
        response = client.get("/api/users/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_multiple_user_registrations(self, app, client):
        """Test multiple user registrations"""
        emails = [
            "user1@example.com",
            "user2@example.com",
            "user3@example.com"
        ]

        user_ids = []
        for email in emails:
            response = client.post(
                "/api/users/register",
                json={"email": email}
            )
            assert response.status_code == 200
            user_ids.append(response.json()["id"])

        # Verify all users exist
        for user_id, email in zip(user_ids, emails):
            response = client.get(f"/api/users/{user_id}")
            assert response.status_code == 200
            assert response.json()["email"] == email

        # Verify all welcome emails were sent
        email_handler = app.state.email_handler
        assert len(email_handler.sent_emails) == 3

    @pytest.mark.asyncio
    async def test_di_container_integration(self, app):
        """Test DI container resolves dependencies correctly"""
        container = app.state.container

        # Resolve UserService
        user_service = container.resolve(UserService)
        assert user_service is not None
        assert isinstance(user_service.event_bus, EventBus)

        # Singleton EventBus should be same instance
        event_bus = container.resolve(EventBus)
        assert event_bus is user_service.event_bus


class TestConcurrentRequests:
    """Test concurrent request handling"""

    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, app, client):
        """Test handling concurrent user registrations"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def register_user(email: str):
            return client.post(
                "/api/users/register",
                json={"email": email}
            )

        # Simulate concurrent requests
        emails = [f"user{i}@example.com" for i in range(10)]

        with ThreadPoolExecutor(max_workers=5) as executor:
            responses = list(executor.map(register_user, emails))

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

        # All users should be retrievable
        for response in responses:
            user_id = response.json()["id"]
            get_response = client.get(f"/api/users/{user_id}")
            assert get_response.status_code == 200

        # All emails should have been sent
        email_handler = app.state.email_handler
        assert len(email_handler.sent_emails) == 10
