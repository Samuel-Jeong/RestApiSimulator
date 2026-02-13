"""Assertion validation engine"""

import re
from typing import Any, Dict, List, Tuple
from ..models.scenario import Assertion, AssertionOperator


class AssertionEngine:
    """Validates response assertions"""
    
    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert camelCase or PascalCase to snake_case"""
        # Insert underscore before uppercase letters and convert to lowercase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def _to_camel_case(text: str) -> str:
        """Convert snake_case to camelCase"""
        components = text.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    @staticmethod
    def _to_pascal_case(text: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(x.title() for x in text.split('_'))
    
    @staticmethod
    def _get_field_from_dict(data: dict, field_name: str) -> Any:
        """
        Try to get field from dict with case-insensitive variations
        
        Args:
            data: Dictionary to search
            field_name: Field name to find
            
        Returns:
            Field value or None if not found
        """
        # Try original field name first
        if field_name in data:
            return data[field_name]
        
        # Try different case variations
        variations = [
            field_name,  # original
            AssertionEngine._to_snake_case(field_name),  # snake_case
            AssertionEngine._to_camel_case(field_name),  # camelCase
            AssertionEngine._to_pascal_case(field_name),  # PascalCase
        ]
        
        for variation in variations:
            if variation in data:
                return data[variation]
        
        return None
    
    @staticmethod
    def get_field_value(data: Any, field_path: str) -> Any:
        """
        Extract value from nested structure using dot notation with case-insensitive field matching
        Example: "body.user.id" -> data["body"]["user"]["id"]
        Supports camelCase, snake_case, PascalCase variations
        """
        if field_path == "status":
            return data.get("status") if isinstance(data, dict) else (data if isinstance(data, int) else None)
        
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = AssertionEngine._get_field_from_dict(current, part)
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                current = current[index] if index < len(current) else None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    @staticmethod
    def validate_assertion(
        assertion: Assertion,
        status_code: int,
        response_body: Any
    ) -> Tuple[bool, str]:
        """
        Validate a single assertion
        
        Returns:
            Tuple of (passed, message)
        """
        # Prepare data structure
        data = {
            "status": status_code,
            "body": response_body
        }
        
        # Extract field value
        actual_value = AssertionEngine.get_field_value(data, assertion.field)
        expected_value = assertion.value
        operator = assertion.operator
        
        # Perform comparison
        try:
            passed = AssertionEngine._compare(actual_value, operator, expected_value)
            
            if passed:
                message = f"✓ {assertion.field} {operator.value} {expected_value}"
            else:
                message = assertion.message or f"✗ {assertion.field}: expected {operator.value} {expected_value}, got {actual_value}"
            
            return passed, message
        
        except Exception as e:
            return False, f"✗ Assertion error: {str(e)}"
    
    @staticmethod
    def _compare(actual: Any, operator: AssertionOperator, expected: Any) -> bool:
        """Perform comparison based on operator"""
        
        if operator == AssertionOperator.EQ:
            return actual == expected
        
        elif operator == AssertionOperator.NE:
            return actual != expected
        
        elif operator == AssertionOperator.GT:
            return actual > expected
        
        elif operator == AssertionOperator.LT:
            return actual < expected
        
        elif operator == AssertionOperator.GTE:
            return actual >= expected
        
        elif operator == AssertionOperator.LTE:
            return actual <= expected
        
        elif operator == AssertionOperator.CONTAINS:
            if isinstance(actual, str):
                return expected in actual
            elif isinstance(actual, (list, tuple)):
                return expected in actual
            return False
        
        elif operator == AssertionOperator.NOT_CONTAINS:
            if isinstance(actual, str):
                return expected not in actual
            elif isinstance(actual, (list, tuple)):
                return expected not in actual
            return True
        
        elif operator == AssertionOperator.IN:
            return actual in expected
        
        elif operator == AssertionOperator.NOT_IN:
            return actual not in expected
        
        elif operator == AssertionOperator.REGEX:
            if isinstance(actual, str) and isinstance(expected, str):
                return bool(re.match(expected, actual))
            return False
        
        elif operator == AssertionOperator.EXISTS:
            return actual is not None
        
        else:
            raise ValueError(f"Unknown operator: {operator}")
    
    @staticmethod
    def validate_all(
        assertions: List[Assertion],
        status_code: int,
        response_body: Any
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Validate all assertions
        
        Returns:
            Tuple of (passed_count, failed_count, details)
        """
        passed = 0
        failed = 0
        details = []
        
        for assertion in assertions:
            is_passed, message = AssertionEngine.validate_assertion(
                assertion, status_code, response_body
            )
            
            if is_passed:
                passed += 1
            else:
                failed += 1
            
            details.append({
                "field": assertion.field,
                "operator": assertion.operator.value,
                "expected": assertion.value,
                "passed": is_passed,
                "message": message
            })
        
        return passed, failed, details

