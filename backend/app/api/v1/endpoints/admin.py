"""
Comprehensive Administrative API Endpoints for TrustGuard AI.
Handles:
- Dedicated Administrator Authentication (/auth/login, /auth/logout, /auth/me)
- Platform Overview Analytics & Activity Charts (/dashboard/stats, /dashboard/activity, /dashboard/events)
- User Management & Suspension Controls (/users, /users/{id}/suspend, /users/{id}/restore)
- Community Threat Report Moderation & Bulk Actions (/reports, /reports/{id}/moderate, /reports/bulk-moderate)
- Threat Intelligence Overview (/threat-intelligence/summary)
- Website-Wide Maintenance Mode (/maintenance)
- Real System Diagnostics & Monitoring (/system/health)
- Immutable Administrator Audit Logging (/audit-logs)
- Admin Security Settings (/settings/change-password)
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.admin_security import get_current_admin, require_admin_role
from app.schemas.admin import (
    AdminAuditLogItem,
    AdminBulkModerationRequest,
    AdminBulkModerationResponse,
    AdminChangePasswordRequest,
    AdminDashboardActivity,
    AdminDashboardStats,
    AdminEventItem,
    AdminLoginRequest,
    AdminReportDetail,
    AdminReportListItem,
    AdminReportModerationAction,
    AdminScanItem,
    AdminThreatIntelSummary,
    AdminTokenResponse,
    AdminUserDeleteRequest,
    AdminUserDetail,
    AdminUserEmailChangeRequest,
    AdminUserListItem,
    AdminUserProfile,
    AdminUserStatusUpdate,
    AdminUserUpdateRequest,
    BulkModerationDetail,
    ContributorCreate,
    ContributorItem,
    ContributorReorderItem,
    ContributorsPageConfig,
    ContributorsPageConfigUpdate,
    ContributorUpdate,
    MaintenanceConfig,
    MaintenanceUpdateRequest,
    PaginatedAdminAuditLogs,
    PaginatedAdminReports,
    PaginatedAdminScans,
    PaginatedAdminUsers,
    SystemHealthResponse,
    SystemSettingsConfig,
    SystemSettingsUpdate,
    WebsitePageCreate,
    WebsitePageItem,
    WebsitePageUpdate,
)
from app.schemas.report import CommunityReportModerationUpdate
from app.services.admin_service import AdminService, get_admin_service

logger = logging.getLogger("trustguard.api.admin")
router = APIRouter()


# -----------------------------------------------------------------------------
# 1. Administrator Authentication
# -----------------------------------------------------------------------------
@router.post(
    "/auth/login",
    response_model=AdminTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Administrator Login",
    description="Authenticates provisioned administrator using username and password with Argon2id verification and rate-limiting.",
)
async def admin_login(
    login_in: AdminLoginRequest,
    request: Request,
    service: AdminService = Depends(get_admin_service),
) -> AdminTokenResponse:
    client_ip = request.client.host if request.client else "127.0.0.1"
    return await service.authenticate_admin(login_in, client_ip)


@router.get(
    "/auth/me",
    response_model=AdminUserProfile,
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated Administrator Profile",
)
async def admin_me(
    admin_user: AdminUserProfile = Depends(get_current_admin),
) -> AdminUserProfile:
    return admin_user


@router.post(
    "/auth/logout",
    status_code=status.HTTP_200_OK,
    summary="Administrator Logout",
)
async def admin_logout(
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, str]:
    await service._repo.log_audit_event(
        action="ADMIN_LOGOUT",
        admin_username=admin_user.username,
        admin_id=admin_user.id,
        target_resource="admin_auth",
        outcome="SUCCESS",
    )
    return {"message": "Administrator session logged out successfully."}


# -----------------------------------------------------------------------------
# 2. Dashboard Analytics & Activity
# -----------------------------------------------------------------------------
@router.get(
    "/dashboard/stats",
    response_model=AdminDashboardStats,
    summary="Admin Dashboard Overview Statistics",
)
async def get_dashboard_stats(
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminDashboardStats:
    return await service.get_dashboard_stats()


@router.get(
    "/dashboard/activity",
    response_model=AdminDashboardActivity,
    summary="Admin Dashboard Activity Time Series",
)
async def get_dashboard_activity(
    days: int = Query(30, ge=7, le=90, description="Time window in days (7, 30, or 90)"),
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminDashboardActivity:
    return await service.get_dashboard_activity(days=days)


@router.get(
    "/dashboard/events",
    response_model=List[AdminEventItem],
    summary="Admin Dashboard Platform Events Feed",
)
async def get_dashboard_events(
    limit: int = Query(15, ge=1, le=50),
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> List[AdminEventItem]:
    return await service.get_recent_events(limit=limit)


# -----------------------------------------------------------------------------
# 3. User Management
# -----------------------------------------------------------------------------
@router.get(
    "/users",
    response_model=PaginatedAdminUsers,
    summary="Admin User Management: List Users",
)
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by email or name"),
    is_active: Optional[bool] = Query(None, description="Filter by status (active/suspended)"),
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> PaginatedAdminUsers:
    return await service.list_users(page, page_size, search, is_active)


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Admin User Management: View User Details",
)
async def admin_get_user_detail(
    user_id: uuid.UUID,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserDetail:
    return await service.get_user_detail(user_id)


@router.post(
    "/users/{user_id}/suspend",
    status_code=status.HTTP_200_OK,
    summary="Admin User Management: Suspend User Account",
)
async def admin_suspend_user(
    user_id: uuid.UUID,
    status_in: AdminUserStatusUpdate,
    request: Request,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else None
    await service.suspend_user(admin_user, user_id, status_in.reason, client_ip)
    return {"success": True, "message": f"User '{user_id}' has been suspended successfully."}


@router.post(
    "/users/{user_id}/restore",
    status_code=status.HTTP_200_OK,
    summary="Admin User Management: Restore User Account",
)
async def admin_restore_user(
    user_id: uuid.UUID,
    status_in: AdminUserStatusUpdate,
    request: Request,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else None
    await service.restore_user(admin_user, user_id, status_in.reason, client_ip)
    return {"success": True, "message": f"User '{user_id}' has been restored successfully."}


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Admin User Management: Update User Profile & Role",
)
async def admin_update_user(
    user_id: uuid.UUID,
    update_in: AdminUserUpdateRequest,
    request: Request,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserDetail:
    client_ip = request.client.host if request.client else None
    return await service.update_user_profile(user_id, update_in, admin_user, client_ip)


@router.post(
    "/users/{user_id}/email",
    response_model=AdminUserDetail,
    summary="Admin User Management: Update Registered User Email",
)
async def admin_update_user_email(
    user_id: uuid.UUID,
    email_in: AdminUserEmailChangeRequest,
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin"])),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserDetail:
    client_ip = request.client.host if request.client else None
    return await service.update_user_email(user_id, email_in, admin_user, client_ip)


@router.delete(
    "/users/{user_id}",
    summary="Admin User Management: Safely Delete User Account",
)
async def admin_delete_user(
    user_id: uuid.UUID,
    request: Request,
    reason: Optional[str] = Query(None, description="Reason for deletion"),
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin"])),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else None
    delete_in = AdminUserDeleteRequest(reason=reason)
    return await service.delete_user_account(user_id, delete_in, admin_user, client_ip)


# -----------------------------------------------------------------------------
# 4. Community Threat Moderation
# -----------------------------------------------------------------------------
@router.get(
    "/reports",
    response_model=PaginatedAdminReports,
    summary="Admin Threat Moderation Queue",
)
async def admin_list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter: PENDING, UNDER_REVIEW, APPROVED, REJECTED, RESOLVED"),
    category: Optional[str] = Query(None, description="Filter: PHISHING, MALWARE, etc."),
    search: Optional[str] = Query(None, description="Search by domain or URL"),
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> PaginatedAdminReports:
    return await service.list_reports(page, page_size, status, category, search)


# Backward compatibility alias
@router.get(
    "/community/reports",
    response_model=PaginatedAdminReports,
    include_in_schema=False,
)
async def admin_list_reports_compat(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    moderation_status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> PaginatedAdminReports:
    return await service.list_reports(page, page_size, moderation_status, category)


@router.patch(
    "/community/reports/{report_id}",
    include_in_schema=False,
)
async def admin_moderate_report_compat(
    report_id: uuid.UUID,
    update_in: CommunityReportModerationUpdate,
    admin_user: AdminUserProfile = Depends(get_current_admin),
) -> Any:
    from app.core.security import AuthenticatedUser
    from app.services.community_reporting_service import get_community_service
    service = get_community_service()
    moderator = AuthenticatedUser(
        user_id=admin_user.id,
        email=admin_user.username,
        role="admin",
    )
    return await service.admin_moderate_report(
        report_id=report_id,
        moderator=moderator,
        update_in=update_in,
    )


@router.get(
    "/reports/{report_id}",
    response_model=AdminReportDetail,
    summary="Admin Threat Moderation: Inspect Single Report",
)
async def admin_get_report_detail(
    report_id: uuid.UUID,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminReportDetail:
    return await service.get_report_detail(report_id)


@router.post(
    "/reports/{report_id}/moderate",
    status_code=status.HTTP_200_OK,
    summary="Admin Threat Moderation: Moderate Report",
)
async def admin_moderate_report(
    report_id: uuid.UUID,
    action_in: AdminReportModerationAction,
    request: Request,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else None
    await service.moderate_report(admin_user, report_id, action_in, client_ip)
    return {
        "success": True,
        "message": f"Threat report '{report_id}' has been marked as '{action_in.action}'.",
    }


@router.post(
    "/reports/bulk-moderate",
    response_model=AdminBulkModerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin Threat Moderation: Bulk Action",
)
async def admin_bulk_moderate_reports(
    bulk_in: AdminBulkModerationRequest,
    request: Request,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminBulkModerationResponse:
    client_ip = request.client.host if request.client else None
    return await service.bulk_moderate_reports(admin_user, bulk_in, client_ip)


# -----------------------------------------------------------------------------
# 5. Threat Intelligence Management
# -----------------------------------------------------------------------------
@router.get(
    "/threat-intelligence/summary",
    response_model=AdminThreatIntelSummary,
    summary="Admin Threat Intelligence Overview",
)
async def admin_threat_intel_summary(
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminThreatIntelSummary:
    return await service.get_threat_intel_summary()


# -----------------------------------------------------------------------------
# 6. Website Maintenance Mode
# -----------------------------------------------------------------------------
@router.get(
    "/maintenance",
    response_model=MaintenanceConfig,
    summary="Admin Maintenance Mode Configuration",
)
async def admin_get_maintenance(
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> MaintenanceConfig:
    return await service.get_maintenance_config()


@router.post(
    "/maintenance",
    response_model=MaintenanceConfig,
    status_code=status.HTTP_200_OK,
    summary="Admin Maintenance Mode: Update Settings",
)
async def admin_update_maintenance(
    update_in: MaintenanceUpdateRequest,
    request: Request,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> MaintenanceConfig:
    client_ip = request.client.host if request.client else None
    return await service.update_maintenance_mode(admin_user, update_in, client_ip)


# -----------------------------------------------------------------------------
# 7. System Diagnostics & Monitoring
# -----------------------------------------------------------------------------
@router.get(
    "/system/health",
    response_model=SystemHealthResponse,
    summary="Admin System Monitoring & Real Diagnostics",
)
async def admin_system_health(
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> SystemHealthResponse:
    return await service.check_system_health()


# -----------------------------------------------------------------------------
# 8. Administrator Audit Logs
# -----------------------------------------------------------------------------
@router.get(
    "/audit-logs",
    response_model=PaginatedAdminAuditLogs,
    summary="Admin Audit Logs",
)
async def admin_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    admin_username: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> PaginatedAdminAuditLogs:
    return await service.get_audit_logs(page, page_size, action, admin_username, search)


# -----------------------------------------------------------------------------
# 9. Admin Settings & Password Change
# -----------------------------------------------------------------------------
@router.post(
    "/settings/change-password",
    status_code=status.HTTP_200_OK,
    summary="Admin Settings: Change Password",
)
async def admin_change_password(
    change_in: AdminChangePasswordRequest,
    request: Request,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, str]:
    client_ip = request.client.host if request.client else None
    await service.change_admin_password(admin_user, change_in, client_ip)
    return {"message": "Administrator password has been successfully updated with Argon2id."}


# -----------------------------------------------------------------------------
# 10. Contributors Management
# -----------------------------------------------------------------------------
@router.get(
    "/contributors",
    response_model=List[ContributorItem],
    summary="Admin: List Project Contributors",
)
async def admin_get_contributors(
    include_inactive: bool = Query(True, description="Whether to include inactive contributors"),
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> List[ContributorItem]:
    return await service.get_contributors(include_inactive=include_inactive)


@router.get(
    "/contributors/{contributor_id}",
    response_model=ContributorItem,
    summary="Admin: Get Contributor Details",
)
async def admin_get_contributor(
    contributor_id: str,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> ContributorItem:
    return await service.get_contributor(contributor_id)


@router.post(
    "/contributors",
    response_model=ContributorItem,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: Create New Contributor",
)
async def admin_create_contributor(
    data: ContributorCreate,
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin", "content_manager"])),
    service: AdminService = Depends(get_admin_service),
) -> ContributorItem:
    client_ip = request.client.host if request.client else None
    return await service.create_contributor(data, admin_user, client_ip)


@router.put(
    "/contributors/{contributor_id}",
    response_model=ContributorItem,
    summary="Admin: Update Contributor Record",
)
async def admin_update_contributor(
    contributor_id: str,
    data: ContributorUpdate,
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin", "content_manager"])),
    service: AdminService = Depends(get_admin_service),
) -> ContributorItem:
    client_ip = request.client.host if request.client else None
    return await service.update_contributor(contributor_id, data, admin_user, client_ip)


@router.delete(
    "/contributors/{contributor_id}",
    summary="Admin: Delete Contributor",
)
async def admin_delete_contributor(
    contributor_id: str,
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin"])),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else None
    return await service.delete_contributor(contributor_id, admin_user, client_ip)


@router.post(
    "/contributors/reorder",
    summary="Admin: Reorder Project Contributors",
)
async def admin_reorder_contributors(
    items: List[ContributorReorderItem],
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin", "content_manager"])),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else None
    return await service.reorder_contributors(items, admin_user, client_ip)


@router.get(
    "/contributors-page-config",
    response_model=ContributorsPageConfig,
    summary="Admin: Get Contributors Page Configuration",
)
async def admin_get_contributors_page_config(
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> ContributorsPageConfig:
    return await service.get_contributors_page_config()


@router.put(
    "/contributors-page-config",
    response_model=ContributorsPageConfig,
    summary="Admin: Update Contributors Page Configuration",
)
async def admin_update_contributors_page_config(
    data: ContributorsPageConfigUpdate,
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin", "content_manager"])),
    service: AdminService = Depends(get_admin_service),
) -> ContributorsPageConfig:
    client_ip = request.client.host if request.client else None
    return await service.update_contributors_page_config(data, admin_user, client_ip)


# -----------------------------------------------------------------------------
# 11. Website Pages (CMS) Management
# -----------------------------------------------------------------------------
@router.get(
    "/pages",
    response_model=List[WebsitePageItem],
    summary="Admin: List Dynamic CMS Pages",
)
async def admin_get_pages(
    include_unpublished: bool = Query(True, description="Whether to include unpublished pages"),
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> List[WebsitePageItem]:
    return await service.get_pages(include_unpublished=include_unpublished)


@router.get(
    "/pages/{page_id}",
    response_model=WebsitePageItem,
    summary="Admin: Get Dynamic Page Details",
)
async def admin_get_page(
    page_id: str,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> WebsitePageItem:
    return await service.get_page_by_id(page_id)


@router.post(
    "/pages",
    response_model=WebsitePageItem,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: Create New CMS Page",
)
async def admin_create_page(
    data: WebsitePageCreate,
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin", "content_manager"])),
    service: AdminService = Depends(get_admin_service),
) -> WebsitePageItem:
    client_ip = request.client.host if request.client else None
    return await service.create_page(data, admin_user, client_ip)


@router.put(
    "/pages/{page_id}",
    response_model=WebsitePageItem,
    summary="Admin: Update CMS Page",
)
async def admin_update_page(
    page_id: str,
    data: WebsitePageUpdate,
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin", "content_manager"])),
    service: AdminService = Depends(get_admin_service),
) -> WebsitePageItem:
    client_ip = request.client.host if request.client else None
    return await service.update_page(page_id, data, admin_user, client_ip)


@router.delete(
    "/pages/{page_id}",
    summary="Admin: Delete CMS Page",
)
async def admin_delete_page(
    page_id: str,
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin"])),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else None
    return await service.delete_page(page_id, admin_user, client_ip)


# -----------------------------------------------------------------------------
# 12. Scans Management
# -----------------------------------------------------------------------------
@router.get(
    "/scans",
    response_model=PaginatedAdminScans,
    summary="Admin: List Scans Across Platform",
)
async def admin_get_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by URL or domain"),
    classification: Optional[str] = Query(None, description="Filter: SAFE, SUSPICIOUS, MALICIOUS"),
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> PaginatedAdminScans:
    return await service.get_scans_list(page, page_size, search, classification)


@router.get(
    "/scans/{scan_id}",
    summary="Admin: Get Detailed Scan Telemetry",
)
async def admin_get_scan_detail(
    scan_id: str,
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    return await service.get_scan_detail(scan_id)


# -----------------------------------------------------------------------------
# 13. System Settings Configuration
# -----------------------------------------------------------------------------
@router.get(
    "/settings/general",
    response_model=SystemSettingsConfig,
    summary="Admin: Get Global System Settings & Branding",
)
async def admin_get_system_settings(
    admin_user: AdminUserProfile = Depends(get_current_admin),
    service: AdminService = Depends(get_admin_service),
) -> SystemSettingsConfig:
    return await service.get_system_settings()


@router.put(
    "/settings/general",
    response_model=SystemSettingsConfig,
    summary="Admin: Update Global System Settings & Branding",
)
async def admin_update_system_settings(
    data: SystemSettingsUpdate,
    request: Request,
    admin_user: AdminUserProfile = Depends(require_admin_role(["super_admin", "admin"])),
    service: AdminService = Depends(get_admin_service),
) -> SystemSettingsConfig:
    client_ip = request.client.host if request.client else None
    return await service.update_system_settings(data, admin_user, client_ip)
