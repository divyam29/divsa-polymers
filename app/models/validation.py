from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class InquiryModel(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    phone: str = Field(..., max_length=15)
    city: str | None = Field(default=None, max_length=50)
    business_info: str | None = Field(default=None)
    quantity_required: str | None = None
    product_id: str | None = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r'^\+?[\d\s-]{10,15}$', v):
             raise ValueError('Invalid phone number format')
        return v.strip()

class ProductModel(BaseModel):
    name: str = Field(..., min_length=2)
    description: str = Field(..., min_length=10)
    type: str
    quality: str
    features: list[str] = Field(default_factory=list)
