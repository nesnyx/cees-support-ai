from typing import Optional
from pydantic import BaseModel, Field


class OrderInput(BaseModel):
    customer_name: str = Field(description="Nama lengkap pelanggan atau nama pelanggan")
    product_name: str = Field(description="nama dari produk yang dipesan")
    quantity: int = Field(description="Jumlah produk yang dipesan")
    level_ice: str = Field(description="Level ice yang dipesan")
    level_sugar: str = Field(description="Level sugar yang dipesan")
    temperature: str = Field(description="Temperatur yang dipesan panas atau dingin")
    status: str = Field(description="Status pemesanan default ON-PROCESS")


class OrderStatusInput(BaseModel):
    order_id: str = Field(description="Order ID pesanan yang akan dicek statusnya")


class OrderSearchInput(BaseModel):
    customer_name: str = Field(description="Nama pelanggan untuk mencari pesanan")
    product_name: str = Field(
        description="Nama produk (opsional untuk mempersempit pencarian)", default=""
    )


# Tambahkan schema baru untuk cancel order
class OrderCancelInput(BaseModel):
    order_id: str = Field(description="ID pesanan yang akan dibatalkan")
    reason: Optional[str] = Field(
        description="Alasan pembatalan (opsional)", default=""
    )
    status: Optional[str] = Field(description="Status pemesanan ", default="CANCELLED")


# Tambahkan schema baru untuk update order
class OrderUpdateInput(BaseModel):
    order_id: str = Field(description="ID pesanan yang akan diupdate")
    customer_name: Optional[str] = Field(
        description="Nama pelanggan baru (opsional)", default=None
    )
    product_name: Optional[str] = Field(
        description="Nama produk baru (opsional)", default=None
    )
    quantity: Optional[int] = Field(
        description="Jumlah produk baru (opsional)", default=None
    )
    level_ice: Optional[str] = Field(
        description="Level ice baru (opsional)", default=None
    )
    level_sugar: Optional[str] = Field(
        description="Level sugar baru (opsional)", default=None
    )
    temperature: Optional[str] = Field(
        description="Temperatur baru (opsional)", default=None
    )


class SendImageProductToCustomer(BaseModel):

    name: str = Field(description="Nama Product yang diambil entah itu dari customer")

    user: str = Field(description="ID pelanggan untuk mencari produk")


class GetProductByUserID(BaseModel):
    user: str = Field(description="ID pelanggan untuk mencari produk")
