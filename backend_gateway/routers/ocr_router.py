"""
OCR router for processing receipt/pantry item images and barcode scanning.
This module provides HTTP endpoints that delegate to the OcrService for business logic.
"""

import base64
import hashlib
import json
import logging
import re
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile
from openai import AuthenticationError

from backend_gateway.core.openai_client import get_openai_client
from backend_gateway.models.ocr_models import (
    BarcodeResponse,
    Base64ImageRequest,
    DebugStatusResponse,
    MockDataConfig,
    OCRResponse,
    ReceiptScanRequest,
)
from backend_gateway.RemoteControl_7 import is_mock_enabled, set_mock
from backend_gateway.services.ocr_service import ocr_service
from backend_gateway.utils.smart_cache import get_cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ocr", tags=["OCR"])


def get_mime_type(image_data: bytes) -> str:
    """Detect MIME type of image data."""
    if image_data.startswith(b'\xff\xd8\xff'):
        return "image/jpeg"
    elif image_data.startswith(b'\x89PNG'):
        return "image/png"
    elif image_data.startswith(b'GIF8'):
        return "image/gif"
    elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:12]:
        return "image/webp"
    else:
        return "image/jpeg"  # Default fallback


def generate_image_hash(image_data: bytes) -> str:
    """Generate SHA256 hash of image data for caching/deduplication."""
    return hashlib.sha256(image_data).hexdigest()


# Utility functions for backward compatibility with existing endpoints
def is_ocr_mock_enabled() -> bool:
    """Check if OCR mock data is enabled"""
    return is_mock_enabled("ocr_scan")


# Mock data and business logic moved to OcrService

# Models moved to backend_gateway.models.ocr_models


@router.post("/scan-items", response_model=OCRResponse)
async def scan_items(file: UploadFile = File(...)):
    """
    Scan items from an uploaded image using OpenAI Vision API or mock data.
    Returns structured data about identified pantry items including proper categorization.
    """
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    try:
        image_data = await file.read()

        # Delegate to service
        result = await ocr_service.process_image(
            image_data, source_info={"endpoint": "scan-items", "filename": file.filename}
        )

        logger.info(f"Scan items completed: {len(result.items)} items detected")
        return result

    except AuthenticationError:
        logger.error("OpenAI authentication failed")
        raise HTTPException(status_code=401, detail="OpenAI authentication failed")
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in scan_items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/scan-receipt", response_model=OCRResponse)
async def scan_receipt(request: ReceiptScanRequest):
    """
    Scan receipt from base64 image data using OpenAI Vision API or mock data.
    This endpoint accepts JSON with image_base64 to match frontend expectations.
    """
    try:
        # Decode base64 image data
        try:
            image_data = base64.b64decode(request.image_base64)
        except Exception as decode_error:
            logger.error(f"Base64 decode error: {decode_error}")
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        # Size check
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="Image too large. Maximum size is 10MB.")

        # Delegate to service
        result = await ocr_service.process_image(
            image_data, source_info={"endpoint": "scan-receipt", "user_id": request.user_id}
        )

        logger.info(f"Receipt scan completed: {len(result.items)} items detected")
        return result

    except AuthenticationError:
        logger.error("OpenAI authentication failed")
        raise HTTPException(status_code=401, detail="OpenAI authentication failed")
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error in scan_receipt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing receipt: {str(e)}")


@router.post("/scan-barcode", response_model=BarcodeResponse)
async def scan_barcode(file: UploadFile = File(...)):
    """
    Scan barcode from an uploaded image using OpenAI Vision API.
    """
    logger.info(f"Starting barcode scan for file: {file.filename}")

    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    try:
        image_data = await file.read()
        logger.info(f"Read image data: {len(image_data)} bytes")

        # Get OpenAI client
        client = get_openai_client()
        if not client:
            logger.error("OpenAI client not available")
            raise HTTPException(status_code=500, detail="OpenAI client not configured")

        mime_type = get_mime_type(image_data)
        processed_image_base64 = base64.b64encode(image_data).decode("utf-8")

        system_prompt = """You are a barcode reader. Look for any barcode (UPC, EAN, QR code, or other) in this image.
        If you find a barcode, return the numbers you can read.
        
        Return a JSON object with:
        - 'barcode': The barcode number as a string (or null if no barcode found)
        - 'type': The type of barcode (UPC, EAN, QR, etc.) if identifiable
        
        If no barcode is visible, return: {"barcode": null, "type": null}
        """

        logger.info("Calling OpenAI API for barcode scan")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{processed_image_base64}",
                                "detail": "high",
                            },
                        }
                    ],
                },
            ],
            max_tokens=300,
        )

        content = response.choices[0].message.content
        logger.debug(f"OpenAI response: {content}")

        try:
            # Extract JSON from response
            json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content

            parsed_json = json.loads(json_str)
            barcode = parsed_json.get("barcode")

            if barcode:
                logger.info(f"Barcode found: {barcode}")
                return BarcodeResponse(
                    success=True, barcode=str(barcode), message="Barcode successfully detected"
                )
            else:
                logger.info("No barcode found in image")
                return BarcodeResponse(
                    success=False, barcode=None, message="No barcode found in the image"
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return BarcodeResponse(
                success=False, barcode=None, message="Could not parse barcode from image analysis"
            )

    except AuthenticationError:
        logger.error("OpenAI authentication failed")
        raise HTTPException(status_code=401, detail="OpenAI authentication failed")
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


# Business logic moved to OcrService

# === DIAGNOSTIC ENDPOINTS ===


@router.get("/debug/status", response_model=DebugStatusResponse)
async def get_debug_status():
    """
    Get comprehensive OCR pipeline status for debugging wrong item detection.
    """
    cache = get_cache()
    cache_stats = cache.get_stats()

    # Check OpenAI client status
    try:
        client = get_openai_client()
        openai_status = "✅ Available"
    except Exception as e:
        openai_status = f"❌ Error: {str(e)}"

    # Get recent detections from service
    recent_detections = ocr_service.get_recent_detections()

    return DebugStatusResponse(
        mock_data_enabled=is_ocr_mock_enabled(),
        cache_stats={
            **cache_stats,
            "ocr_cache_entries": len([k for k in cache.cache.keys() if "ocr_scan_" in k]),
        },
        openai_client_status=openai_status,
        recent_detections=len(recent_detections),
        image_hash_examples=[d.get("image_hash", "") for d in recent_detections[:3]],
    )


@router.get("/debug/recent-detections")
async def get_recent_detections():
    """
    Get recent detection results for debugging.
    """
    recent_detections = ocr_service.get_recent_detections()
    return {"recent_detections": recent_detections, "total_count": len(recent_detections)}


@router.post("/debug/clear-cache")
async def clear_ocr_cache():
    """
    Clear OCR-related cache entries to force fresh detection.
    """
    try:
        # Delegate to service
        result = ocr_service.clear_cache()
        return result

    except Exception as e:
        logger.error(f"Error clearing OCR cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.post("/debug/test-detection")
async def test_detection_pipeline():
    """
    Test the detection pipeline with various scenarios.
    """
    test_results = []

    # Test 1: Mock data status
    mock_enabled = is_ocr_mock_enabled()
    test_results.append(
        {
            "test": "Mock Data Check",
            "status": "✅ PASS" if not mock_enabled else "⚠️  WARNING",
            "result": f"Mock data is {'enabled' if mock_enabled else 'disabled'}",
            "recommendation": (
                "Disable mock data for real detection"
                if mock_enabled
                else "Mock data properly disabled"
            ),
        }
    )

    # Test 2: OpenAI client
    try:
        client = get_openai_client()
        openai_test = {
            "test": "OpenAI Client",
            "status": "✅ PASS",
            "result": "Client available",
            "recommendation": "OpenAI integration ready",
        }
    except Exception as e:
        openai_test = {
            "test": "OpenAI Client",
            "status": "❌ FAIL",
            "result": f"Error: {str(e)}",
            "recommendation": "Fix OpenAI API key configuration",
        }
    test_results.append(openai_test)

    # Test 3: Cache system
    cache = get_cache()
    cache_stats = cache.get_stats()
    test_results.append(
        {
            "test": "Cache System",
            "status": "✅ PASS",
            "result": f"Cache operational with {cache_stats['size']} entries",
            "recommendation": "Cache system working normally",
        }
    )

    # Test 4: Image hash consistency
    test_data = b"test_image_content"
    hash1 = generate_image_hash(test_data)
    hash2 = generate_image_hash(test_data)
    test_results.append(
        {
            "test": "Image Hash Consistency",
            "status": "✅ PASS" if hash1 == hash2 else "❌ FAIL",
            "result": f"Hashes match: {hash1 == hash2}",
            "recommendation": (
                "Image hashing working correctly" if hash1 == hash2 else "Fix image hash generation"
            ),
        }
    )

    return {
        "test_summary": {
            "total_tests": len(test_results),
            "passed": len([t for t in test_results if "✅ PASS" in t["status"]]),
            "warnings": len([t for t in test_results if "⚠️ " in t["status"]]),
            "failed": len([t for t in test_results if "❌ FAIL" in t["status"]]),
        },
        "test_results": test_results,
        "recommendations": [
            "🔄 Clear cache if getting stale results",
            "🎭 Disable mock data for real detection testing",
            "🤖 Ensure OpenAI API key is properly configured",
            "📸 Use different images to test detection accuracy",
            "🔍 Check recent detections endpoint to monitor results",
        ],
    }


@router.post("/debug/force-fresh-detection")
async def force_fresh_detection(file: UploadFile = File(...)):
    """
    Force fresh detection by bypassing cache and mock data.
    """
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    try:
        image_data = await file.read()

        # Clear cache first
        ocr_service.clear_cache()

        # Temporarily disable mock data
        original_mock_state = is_ocr_mock_enabled()
        if original_mock_state:
            set_mock("ocr_scan", False)

        try:
            # Force fresh detection using service
            result = await ocr_service.process_image(
                image_data,
                source_info={"endpoint": "force-fresh-detection", "filename": file.filename},
            )

            # Add debugging info
            if result.debug_info:
                result.debug_info["forced_fresh"] = True
                result.debug_info["cache_bypassed"] = True
                result.debug_info["mock_temporarily_disabled"] = original_mock_state

            return result

        finally:
            # Restore original mock state
            if original_mock_state:
                set_mock("ocr_scan", True)

    except Exception as e:
        logger.error(f"Error in forced fresh detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in forced detection: {str(e)}")


# === CONFIGURATION ENDPOINTS ===


@router.post("/configure-mock-data", summary="Toggle mock data usage")
async def configure_mock_data(config: MockDataConfig):
    """Toggle the use of mock data for OCR endpoints"""
    # Update RemoteControl instead of local variable
    set_mock("ocr_scan", config.use_mock_data)
    logger.info(f"Mock data {'enabled' if config.use_mock_data else 'disabled'}")
    return {
        "success": True,
        "use_mock_data": config.use_mock_data,
        "message": f"Mock data {'enabled' if config.use_mock_data else 'disabled'}",
    }


@router.get("/mock-data-status", summary="Get current mock data status")
async def get_mock_data_status():
    """Get the current status of mock data status"""
    return {
        "use_mock_data": is_ocr_mock_enabled(),
        "message": f"Mock data is {'enabled' if is_ocr_mock_enabled() else 'disabled'}",
    }
