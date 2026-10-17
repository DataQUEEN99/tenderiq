from enum import Enum


class Role(str, Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    MEMBER = "Member"
    VIEWER = "Viewer"


class Permission(str, Enum):
    ORG_CREATE = "org:create"
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_DELETE = "org:delete"

    USER_INVITE = "user:invite"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ROLE = "user:role"

    COMPANY_READ = "company:read"
    COMPANY_UPDATE = "company:update"
    COMPANY_DOC_UPLOAD = "company:doc:upload"
    COMPANY_DOC_DELETE = "company:doc:delete"

    DOC_UPLOAD = "doc:upload"
    DOC_READ = "doc:read"
    DOC_UPDATE = "doc:update"
    DOC_DOWNLOAD = "doc:download"
    DOC_DELETE = "doc:delete"
    DOC_REPROCESS = "doc:reprocess"

    TENDER_CREATE = "tender:create"
    TENDER_READ = "tender:read"
    TENDER_UPDATE = "tender:update"
    TENDER_DELETE = "tender:delete"
    TENDER_DOC_ATTACH = "tender:doc:attach"
    TENDER_DOC_DETACH = "tender:doc:detach"
    TENDER_STATUS = "tender:status"

    PROPOSAL_GENERATE = "proposal:generate"
    PROPOSAL_READ = "proposal:read"
    PROPOSAL_UPDATE = "proposal:update"
    PROPOSAL_EXPORT = "proposal:export"
    PROPOSAL_VERSION = "proposal:version"

    CHAT_CREATE = "chat:create"
    CHAT_READ = "chat:read"
    CHAT_MESSAGE = "chat:message"

    EXPORT_PDF = "export:pdf"
    EXPORT_DOCX = "export:docx"

    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],
    Role.MANAGER: [
        Permission.ORG_READ,
        Permission.USER_INVITE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_ROLE,
        Permission.COMPANY_READ, Permission.COMPANY_UPDATE, Permission.COMPANY_DOC_UPLOAD, Permission.COMPANY_DOC_DELETE,
        Permission.DOC_UPLOAD, Permission.DOC_READ, Permission.DOC_UPDATE, Permission.DOC_DOWNLOAD, Permission.DOC_DELETE, Permission.DOC_REPROCESS,
        Permission.TENDER_CREATE, Permission.TENDER_READ, Permission.TENDER_UPDATE, Permission.TENDER_DELETE,
        Permission.TENDER_DOC_ATTACH, Permission.TENDER_DOC_DETACH, Permission.TENDER_STATUS,
        Permission.PROPOSAL_GENERATE, Permission.PROPOSAL_READ, Permission.PROPOSAL_UPDATE, Permission.PROPOSAL_EXPORT, Permission.PROPOSAL_VERSION,
        Permission.CHAT_CREATE, Permission.CHAT_READ, Permission.CHAT_MESSAGE,
        Permission.EXPORT_PDF, Permission.EXPORT_DOCX,
        Permission.AUDIT_READ,
    ],
    Role.MEMBER: [
        Permission.ORG_READ,
        Permission.USER_READ,
        Permission.COMPANY_READ, Permission.COMPANY_DOC_UPLOAD,
        Permission.DOC_UPLOAD, Permission.DOC_READ, Permission.DOC_DOWNLOAD,
        Permission.TENDER_CREATE, Permission.TENDER_READ, Permission.TENDER_UPDATE,
        Permission.TENDER_DOC_ATTACH, Permission.TENDER_DOC_DETACH,
        Permission.PROPOSAL_GENERATE, Permission.PROPOSAL_READ, Permission.PROPOSAL_UPDATE,
        Permission.CHAT_CREATE, Permission.CHAT_READ, Permission.CHAT_MESSAGE,
        Permission.EXPORT_PDF, Permission.EXPORT_DOCX,
    ],
    Role.VIEWER: [
        Permission.ORG_READ,
        Permission.USER_READ,
        Permission.COMPANY_READ,
        Permission.DOC_READ, Permission.DOC_DOWNLOAD,
        Permission.TENDER_READ,
        Permission.PROPOSAL_READ,
        Permission.CHAT_READ,
        Permission.EXPORT_PDF, Permission.EXPORT_DOCX,
    ],
}


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])


def get_role_permissions(role: Role) -> list[Permission]:
    return ROLE_PERMISSIONS.get(role, [])