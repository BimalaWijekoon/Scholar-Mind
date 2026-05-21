"""
Validators - Input validation utilities
"""

from typing import Optional, List, Set
import re
from urllib.parse import urlparse


class ValidationError(Exception):
    """Validation error with details."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


# Allowed file types
ALLOWED_FILE_TYPES: Set[str] = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/html",
    "application/json",
    "application/xml",
}

ALLOWED_EXTENSIONS: Set[str] = {
    ".pdf",
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".json",
    ".xml",
}

# Max file size (50MB)
MAX_FILE_SIZE: int = 50 * 1024 * 1024


def validate_url(url: str) -> bool:
    """
    Validate a URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if not url:
        raise ValidationError("URL is required", "url")
    
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in ("http", "https"):
            raise ValidationError(
                "URL must use http or https scheme",
                "url",
            )
        
        if not parsed.netloc:
            raise ValidationError("URL must have a valid host", "url")
        
        return True
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid URL: {e}", "url")


def validate_file_type(
    file_type: str,
    filename: Optional[str] = None,
) -> bool:
    """
    Validate file type.
    
    Args:
        file_type: MIME type
        filename: Optional filename for extension check
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if not file_type:
        raise ValidationError("File type is required", "file_type")
    
    if file_type not in ALLOWED_FILE_TYPES:
        raise ValidationError(
            f"File type '{file_type}' is not allowed. "
            f"Allowed types: {', '.join(ALLOWED_FILE_TYPES)}",
            "file_type",
        )
    
    if filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"File extension '{ext}' is not allowed. "
                f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}",
                "filename",
            )
    
    return True


def validate_file_size(size: int) -> bool:
    """
    Validate file size.
    
    Args:
        size: File size in bytes
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If too large
    """
    if size > MAX_FILE_SIZE:
        raise ValidationError(
            f"File size exceeds maximum allowed ({MAX_FILE_SIZE // (1024*1024)}MB)",
            "file",
        )
    
    return True


def validate_document_id(doc_id: str) -> bool:
    """
    Validate a document ID.
    
    Args:
        doc_id: Document ID to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if not doc_id:
        raise ValidationError("Document ID is required", "document_id")
    
    # UUID format
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    
    if not re.match(uuid_pattern, doc_id.lower()):
        raise ValidationError(
            "Document ID must be a valid UUID",
            "document_id",
        )
    
    return True


def validate_query(
    query: str,
    min_length: int = 1,
    max_length: int = 10000,
) -> bool:
    """
    Validate a search/question query.
    
    Args:
        query: Query string
        min_length: Minimum length
        max_length: Maximum length
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if not query:
        raise ValidationError("Query is required", "query")
    
    query = query.strip()
    
    if len(query) < min_length:
        raise ValidationError(
            f"Query must be at least {min_length} characters",
            "query",
        )
    
    if len(query) > max_length:
        raise ValidationError(
            f"Query must not exceed {max_length} characters",
            "query",
        )
    
    return True


def validate_pagination(
    skip: int = 0,
    limit: int = 50,
    max_limit: int = 100,
) -> bool:
    """
    Validate pagination parameters.
    
    Args:
        skip: Number to skip
        limit: Number to return
        max_limit: Maximum allowed limit
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if skip < 0:
        raise ValidationError("Skip must be non-negative", "skip")
    
    if limit < 1:
        raise ValidationError("Limit must be at least 1", "limit")
    
    if limit > max_limit:
        raise ValidationError(
            f"Limit must not exceed {max_limit}",
            "limit",
        )
    
    return True


def validate_entity_type(entity_type: str) -> bool:
    """
    Validate an entity type.
    
    Args:
        entity_type: Entity type string
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    allowed_types = {
        "PERSON",
        "ORGANIZATION",
        "LOCATION",
        "DATE",
        "CONCEPT",
        "GENE",
        "PROTEIN",
        "CHEMICAL",
        "DISEASE",
        "DRUG",
        "SPECIES",
        "CELL_TYPE",
        "METHOD",
        "TECHNOLOGY",
    }
    
    if not entity_type:
        raise ValidationError("Entity type is required", "entity_type")
    
    entity_type_upper = entity_type.upper()
    
    if entity_type_upper not in allowed_types:
        raise ValidationError(
            f"Entity type '{entity_type}' is not recognized. "
            f"Allowed types: {', '.join(sorted(allowed_types))}",
            "entity_type",
        )
    
    return True


def validate_email(email: str) -> bool:
    """
    Validate an email address.
    
    Args:
        email: Email address
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if not email:
        raise ValidationError("Email is required", "email")
    
    # Basic email pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    if not re.match(pattern, email):
        raise ValidationError("Invalid email address", "email")
    
    return True


def validate_password(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = False,
) -> bool:
    """
    Validate a password.
    
    Args:
        password: Password to validate
        min_length: Minimum length
        require_uppercase: Require uppercase letter
        require_lowercase: Require lowercase letter
        require_digit: Require digit
        require_special: Require special character
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if not password:
        raise ValidationError("Password is required", "password")
    
    if len(password) < min_length:
        raise ValidationError(
            f"Password must be at least {min_length} characters",
            "password",
        )
    
    if require_uppercase and not re.search(r"[A-Z]", password):
        raise ValidationError(
            "Password must contain at least one uppercase letter",
            "password",
        )
    
    if require_lowercase and not re.search(r"[a-z]", password):
        raise ValidationError(
            "Password must contain at least one lowercase letter",
            "password",
        )
    
    if require_digit and not re.search(r"\d", password):
        raise ValidationError(
            "Password must contain at least one digit",
            "password",
        )
    
    if require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError(
            "Password must contain at least one special character",
            "password",
        )
    
    return True


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input.
    
    Args:
        text: Text to sanitize
        max_length: Optional maximum length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Limit length
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', "_", filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")
    
    # Ensure it's not empty
    if not filename:
        return "unnamed"
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        max_name_len = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_len] + ("." + ext if ext else "")
    
    return filename
