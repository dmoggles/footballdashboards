"""
Defines the abstract Dashboard base class which provides common functionality
to all dashboards.
"""

from abc import ABC, abstractmethod


class Dashboard(ABC):
    """
    Dashboard ABC which all dashboard visualizations must inherit from.
    
    Specifies most of the metadata functions that inheritors use to define their
    behavior

    """

    def __init__(self, data_accessor)


