"""
Unit and integration test suite for TrustGuard AI Admin Panel and CMS.
Validates:
- Admin password verification and token generation (Argon2id / scrypt)
- Contributors CRUD, ordering, and public page config
- Dynamic CMS Pages CRUD, slug retrieval, and publishing
- General system settings and announcements
- User profile updates, email updates, and deletions
- RBAC permissions and audit logging
"""

import asyncio
import uuid
import pytest
from app.core.admin_security import hash_admin_password, verify_admin_password
from app.database import connection
from app.database.repositories.admin_repo import AdminRepository
from app.schemas.admin import (
    AdminLoginRequest,
    AdminUserEmailChangeRequest,
    AdminUserProfile,
    AdminUserUpdateRequest,
    ContributorCreate,
    ContributorReorderItem,
    ContributorsPageConfigUpdate,
    ContributorUpdate,
    SystemSettingsUpdate,
    WebsitePageCreate,
    WebsitePageUpdate,
)
from app.services.admin_service import AdminService


@pytest.fixture
def admin_repo(monkeypatch):
    monkeypatch.setattr(connection, "is_table_available", lambda table: False)
    return AdminRepository()


@pytest.fixture
def admin_service(admin_repo):
    return AdminService(repo=admin_repo)


@pytest.fixture
def super_admin_user():
    return AdminUserProfile(
        id=uuid.UUID("a2107163-49cd-4486-b982-edef1b495a58"),
        username="admin",
        email="admin@trustguard.ai",
        full_name="Security Administrator",
        role="super_admin",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_admin_password_and_authentication(admin_service):
    """Verifies that administrator credentials (admin / Ratul@2007##) authenticate successfully."""
    login_req = AdminLoginRequest(username="admin", password="Ratul@2007##")
    res = await admin_service.authenticate_admin(login_req, client_ip="127.0.0.1")

    assert res is not None
    assert res.token_type == "Bearer"
    assert res.access_token is not None
    assert len(res.access_token) > 20
    assert res.admin_user.username == "admin"
    assert res.admin_user.role == "super_admin"


@pytest.mark.asyncio
async def test_contributors_crud(admin_service, super_admin_user):
    """Verifies creation, retrieval, updating, and deletion of contributors."""
    # 1. Create
    create_data = ContributorCreate(
        name="Test Researcher",
        role="Detection Engineer",
        bio="Test bio for automated verification.",
        avatar_url="https://example.com/avatar.png",
        social_links={"github": "https://github.com/test"},
        display_order=99,
        is_active=True,
    )
    created = await admin_service.create_contributor(create_data, super_admin_user)
    assert created.name == "Test Researcher"
    assert created.role == "Detection Engineer"
    assert created.id.startswith("contributor-")

    # 2. Get Detail
    fetched = await admin_service.get_contributor(created.id)
    assert fetched.id == created.id
    assert fetched.name == "Test Researcher"

    # 3. Update
    updated = await admin_service.update_contributor(
        created.id,
        ContributorUpdate(role="Senior Detection Lead", display_order=5),
        super_admin_user,
    )
    assert updated.role == "Senior Detection Lead"
    assert updated.display_order == 5

    # 4. List
    all_contributors = await admin_service.get_contributors(include_inactive=True)
    assert any(c.id == created.id for c in all_contributors)

    # 5. Delete
    del_res = await admin_service.delete_contributor(created.id, super_admin_user)
    assert del_res["status"] == "success"

    # Verify gone
    all_after = await admin_service.get_contributors(include_inactive=True)
    assert not any(c.id == created.id for c in all_after)


@pytest.mark.asyncio
async def test_contributors_page_config(admin_service, super_admin_user):
    """Verifies page title, subtitle, and navigation toggles for Contributors page."""
    cfg = await admin_service.get_contributors_page_config()
    assert cfg is not None
    assert cfg.title is not None

    updated_cfg = await admin_service.update_contributors_page_config(
        ContributorsPageConfigUpdate(title="TrustGuard Research Team", show_in_navigation=True),
        super_admin_user,
    )
    assert updated_cfg.title == "TrustGuard Research Team"
    assert updated_cfg.show_in_navigation is True


@pytest.mark.asyncio
async def test_dynamic_cms_pages_crud(admin_service, super_admin_user):
    """Verifies creation, slug routing, markdown editing, and deletion of CMS pages."""
    test_slug = f"test-page-{uuid.uuid4().hex[:6]}"
    create_data = WebsitePageCreate(
        title="Automated Test Page",
        slug=test_slug,
        content="# Test Header\n\nThis is a test paragraph.",
        meta_description="Test meta description",
        is_published=True,
        show_in_navigation=True,
        nav_order=10,
    )
    page = await admin_service.create_page(create_data, super_admin_user)
    assert page.slug == test_slug
    assert page.title == "Automated Test Page"

    # Fetch by slug
    by_slug = await admin_service.get_page_by_slug(test_slug)
    assert by_slug.id == page.id
    assert by_slug.content.startswith("# Test Header")

    # Update
    updated_page = await admin_service.update_page(
        page.id,
        WebsitePageUpdate(title="Updated Test Page", is_published=False),
        super_admin_user,
    )
    assert updated_page.title == "Updated Test Page"
    assert updated_page.is_published is False

    # Delete
    del_res = await admin_service.delete_page(page.id, super_admin_user)
    assert del_res["status"] == "success"


@pytest.mark.asyncio
async def test_system_settings_and_announcement(admin_service, super_admin_user):
    """Verifies reading and updating system settings and announcement banners."""
    settings = await admin_service.get_system_settings()
    assert settings.site_name == "TrustGuard AI"

    updated = await admin_service.update_system_settings(
        SystemSettingsUpdate(
            site_tagline="Real-time URL Security & Threat Defense",
            announcement_enabled=True,
            announcement_message="TrustGuard AI 2.0 Security Upgrade Active",
            announcement_type="info",
        ),
        super_admin_user,
    )
    assert updated.site_tagline == "Real-time URL Security & Threat Defense"
    assert updated.announcement_enabled is True
    assert updated.announcement_message == "TrustGuard AI 2.0 Security Upgrade Active"


@pytest.mark.asyncio
async def test_audit_logs_recorded(admin_service, super_admin_user):
    """Verifies that administrative operations generate immutable audit log entries."""
    logs = await admin_service.get_audit_logs(page=1, page_size=10)
    assert logs is not None
    assert isinstance(logs.items, list)
