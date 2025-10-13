"""Parameter definitions for Vega Web Framework"""

from typing import Any, Optional


class Query:
    """
    Query parameter definition for route handlers.

    Similar to FastAPI's Query, this class allows you to define query parameters
    with validation, default values, and documentation.

    Args:
        default: Default value if parameter is not provided
        alias: Alternative name for the parameter in the query string
        title: Title for documentation
        description: Description for documentation
        gt: Greater than validation
        ge: Greater than or equal validation
        lt: Less than validation
        le: Less than or equal validation
        min_length: Minimum string length
        max_length: Maximum string length
        pattern: Regex pattern for string validation

    Example:
        @router.get("/users")
        async def list_users(
            limit: int = Query(10, ge=1, le=100, description="Maximum number of results")
        ):
            return {"users": [], "limit": limit}
    """

    def __init__(
        self,
        default: Any = None,
        *,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
    ):
        self.default = default
        self.alias = alias
        self.title = title
        self.description = description
        self.gt = gt
        self.ge = ge
        self.lt = lt
        self.le = le
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern

    def validate(self, value: Any, param_name: str) -> Any:
        """
        Validate the parameter value.

        Args:
            value: The value to validate
            param_name: Name of the parameter (for error messages)

        Returns:
            Validated value

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            return self.default

        # Numeric validations
        if isinstance(value, (int, float)):
            if self.gt is not None and value <= self.gt:
                raise ValueError(f"{param_name} must be greater than {self.gt}")
            if self.ge is not None and value < self.ge:
                raise ValueError(f"{param_name} must be greater than or equal to {self.ge}")
            if self.lt is not None and value >= self.lt:
                raise ValueError(f"{param_name} must be less than {self.lt}")
            if self.le is not None and value > self.le:
                raise ValueError(f"{param_name} must be less than or equal to {self.le}")

        # String validations
        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                raise ValueError(f"{param_name} must be at least {self.min_length} characters")
            if self.max_length is not None and len(value) > self.max_length:
                raise ValueError(f"{param_name} must be at most {self.max_length} characters")
            if self.pattern is not None:
                import re
                if not re.match(self.pattern, value):
                    raise ValueError(f"{param_name} does not match pattern {self.pattern}")

        return value


__all__ = ["Query"]
