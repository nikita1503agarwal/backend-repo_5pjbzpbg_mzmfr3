"""
Database Schemas for Interior Quotation System

Each Pydantic model below represents a MongoDB collection. The collection
name is the lowercase of the class name (e.g., User -> "user").
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class User(BaseModel):
    """
    Users of the system (admin or employee)
    Collection: "user"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    role: str = Field(..., pattern="^(admin|employee)$", description="User role")
    phone: Optional[str] = Field(None, description="Phone number")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL")
    is_active: bool = Field(True, description="Whether user is active")

class HouseCategory(BaseModel):
    """
    High-level category of house types (e.g., Apartment, Villa)
    Collection: "housecategory"
    """
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Details about category")

class Subcategory(BaseModel):
    """
    Sub category under a house category (e.g., 1BHK, 2BHK) or types like Kitchen, Bedroom
    Collection: "subcategory"
    """
    name: str = Field(..., description="Subcategory name")
    house_category_id: str = Field(..., description="Reference to house category _id as string")
    description: Optional[str] = Field(None, description="Details about subcategory")

class Package(BaseModel):
    """
    Interior design packages (e.g., Basic, Premium) that can be attached to a subcategory
    Collection: "package"
    """
    name: str = Field(..., description="Package name")
    subcategory_id: str = Field(..., description="Reference to subcategory _id as string")
    price: float = Field(..., ge=0, description="Base price")
    features: List[str] = Field(default_factory=list, description="Feature list")
    description: Optional[str] = Field(None, description="Package description")

class QuotationItem(BaseModel):
    """
    Line item inside a quotation
    """
    package_id: str = Field(..., description="Selected package id as string")
    quantity: int = Field(1, ge=1, description="Quantity")
    unit_price: float = Field(..., ge=0, description="Unit price at time of quote")
    note: Optional[str] = None

class Quotation(BaseModel):
    """
    Generated quotation by an employee for a client
    Collection: "quotation"
    """
    employee_id: str = Field(..., description="User _id of employee as string")
    client_name: str = Field(...)
    client_email: Optional[EmailStr] = None
    house_category_id: str = Field(...)
    subcategory_id: str = Field(...)
    items: List[QuotationItem] = Field(default_factory=list)
    discount_percent: float = Field(0, ge=0, le=100)
    notes: Optional[str] = None

    
# The Flames database viewer will automatically read these schemas
# from GET /schema endpoint if implemented.
