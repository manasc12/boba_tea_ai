from pydantic import BaseModel, Field
from enum import Enum

class Product(BaseModel):
    product_id: int = Field(..., description="The unique identifier of the product.")
    name: str = Field(..., description="The name of the product.")
    category: str = Field(..., description="The category of the product.")
    description: str = Field(..., description="A brief description of the product.")

class Size(str, Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
class ProductPriceSize(BaseModel):
    product_id: int = Field(..., description="The unique identifier of the product.")
    price: float = Field(..., description="The price of the product in EUR.")
    size: Size = Field(..., description="Available size for the product.")

class Order(BaseModel):
    product_id: int = Field(..., description="The ID of the product to order.")
    price: float = Field(..., description="The price of the product in EUR.")
    size: Size = Field(..., description="The size of the product.")
    quantity: int = Field(..., description="The quantity of the product.")

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class OrderResponse(BaseModel):
    order_id: int = Field(..., description="The ID of the created order.")
    status: ApprovalStatus = Field(..., description="The status of the created order.")
    total_price: float = Field(..., description="The total price of the created order in EUR.")

class OrderDetails(BaseModel):
    order_id: int = Field(..., description="The ID of the order.")
    product_id: int = Field(..., description="The ID of the product in the order.")
    price: float = Field(..., description="The price of the product in the order in EUR.")
    size: Size = Field(..., description="The size of the product in the order.")
    quantity: int = Field(..., description="The quantity of the product in the order.")