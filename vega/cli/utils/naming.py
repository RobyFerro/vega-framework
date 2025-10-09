"""Naming convention utilities for code generation"""
import re


def to_snake_case(name: str) -> str:
    """Convert CamelCase/PascalCase to snake_case (standalone function for convenience)"""
    return NamingConverter.to_snake_case(name)


def to_pascal_case(name: str) -> str:
    """Convert any format to PascalCase (standalone function for convenience)"""
    return NamingConverter.to_pascal_case(name)


def to_camel_case(name: str) -> str:
    """Convert any format to camelCase (standalone function for convenience)"""
    return NamingConverter.to_camel_case(name)


def to_kebab_case(name: str) -> str:
    """Convert any format to kebab-case (standalone function for convenience)"""
    return NamingConverter.to_kebab_case(name)


class NamingConverter:
    """Utility class for converting between naming conventions"""

    @staticmethod
    def to_snake_case(name: str) -> str:
        """
        Convert CamelCase or PascalCase to snake_case.

        Args:
            name: String in CamelCase or PascalCase

        Returns:
            String in snake_case

        Examples:
            >>> NamingConverter.to_snake_case("UserRepository")
            'user_repository'
            >>> NamingConverter.to_snake_case("GetUserById")
            'get_user_by_id'
        """
        # Insert underscore before uppercase letters followed by lowercase
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before uppercase letters preceded by lowercase or digits
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        return name.lower()

    @staticmethod
    def to_pascal_case(name: str) -> str:
        """
        Convert strings to PascalCase, handling separators and camelCase input.

        Args:
            name: String in any format (snake_case, kebab-case, space-separated, camelCase)

        Returns:
            String in PascalCase

        Examples:
            >>> NamingConverter.to_pascal_case("user_repository")
            'UserRepository'
            >>> NamingConverter.to_pascal_case("get-user-by-id")
            'GetUserById'
            >>> NamingConverter.to_pascal_case("create user")
            'CreateUser'
        """
        cleaned = name.strip()
        if not cleaned:
            return ""

        # Normalize common separators to spaces
        normalized = cleaned.replace('-', ' ').replace('_', ' ')

        # If we have spaces, split and capitalize each part
        if ' ' in normalized:
            parts = normalized.split()
        else:
            # Handle camelCase or PascalCase input by finding word boundaries
            parts = re.findall(
                r'[A-Z]+(?=$|[A-Z][a-z0-9])|[A-Z]?[a-z0-9]+|[0-9]+',
                cleaned
            )
            if not parts:
                parts = [cleaned]

        def _pascal_piece(piece: str) -> str:
            """Capitalize first letter, lowercase the rest unless all caps"""
            return piece if piece.isupper() else piece[:1].upper() + piece[1:].lower()

        return ''.join(_pascal_piece(part) for part in parts if part)

    @staticmethod
    def to_kebab_case(name: str) -> str:
        """
        Convert to kebab-case.

        Args:
            name: String in any format

        Returns:
            String in kebab-case

        Examples:
            >>> NamingConverter.to_kebab_case("UserRepository")
            'user-repository'
            >>> NamingConverter.to_kebab_case("get_user_by_id")
            'get-user-by-id'
        """
        # First convert to snake_case, then replace underscores with hyphens
        snake = NamingConverter.to_snake_case(name)
        return snake.replace('_', '-')

    @staticmethod
    def to_camel_case(name: str) -> str:
        """
        Convert to camelCase.

        Args:
            name: String in any format

        Returns:
            String in camelCase

        Examples:
            >>> NamingConverter.to_camel_case("UserRepository")
            'userRepository'
            >>> NamingConverter.to_camel_case("get_user_by_id")
            'getUserById'
        """
        pascal = NamingConverter.to_pascal_case(name)
        return pascal[:1].lower() + pascal[1:] if pascal else ""
