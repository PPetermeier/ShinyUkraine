"""
Makes the financial page directory a Python package and exposes the page components.
"""

from .financial_aid_page import financial_page_ui, FinancialPageServer

__all__ = [
    'financial_page_ui',
    'FinancialPageServer'
]