"""
OCR-related Pydantic models for request/response handling.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ParsedItem(BaseModel):
    """Represents a single parsed item from OCR processing."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    quantity: float
    unit: str
    category: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    product_name: Optional[str] = None
    nutrition_info: Optional[Dict[str, Any]] = None
    expiration_date: Optional[str] = None


class OCRResponse(BaseModel):
    """Response model for OCR processing endpoints."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    items: List[ParsedItem]
    raw_text: Optional[str] = None
    message: str = ""
    debug_info: Optional[Dict[str, Any]] = None


class BarcodeResponse(BaseModel):
    """Response model for barcode scanning."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    barcode: Optional[str] = None
    message: str = ""


class ReceiptScanRequest(BaseModel):
    """Request model for receipt scanning with base64 image data."""

    model_config = ConfigDict(from_attributes=True)

    image_base64: str
    user_id: Optional[int] = None


class Base64ImageRequest(BaseModel):
    """Generic request model for base64 image data."""

    model_config = ConfigDict(from_attributes=True)

    image_base64: str


class MockDataConfig(BaseModel):
    """Configuration model for toggling mock data."""

    model_config = ConfigDict(from_attributes=True)

    use_mock_data: bool


class DebugStatusResponse(BaseModel):
    """Response model for debug status information."""

    model_config = ConfigDict(from_attributes=True)

    mock_data_enabled: bool
    cache_stats: Dict[str, Any]
    openai_client_status: str
    recent_detections: int
    image_hash_examples: List[str]
