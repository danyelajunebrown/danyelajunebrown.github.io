"""
Garment Keypoint Detection Module

Automatically detects key measurement points on flat-laid garments
using computer vision (edge detection, contour analysis, heuristics).

Supported garment types:
- pants/jeans/leggings
- shirts/tops (coming soon)
- dresses/skirts (coming soon)
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class GarmentType(Enum):
    PANTS = "pants"
    SHIRT = "shirt"
    DRESS = "dress"
    SKIRT = "skirt"
    UNKNOWN = "unknown"


@dataclass
class Keypoint:
    """A detected keypoint on the garment."""
    name: str
    x: float
    y: float
    confidence: float = 1.0


@dataclass
class Measurement:
    """A calculated measurement between keypoints."""
    name: str
    value_px: float  # in pixels
    value_cm: float  # in centimeters (if scale provided)
    start_point: str
    end_point: str


@dataclass
class DetectionResult:
    """Result of garment detection."""
    success: bool
    garment_type: GarmentType
    keypoints: List[Keypoint]
    measurements: Dict[str, float]
    contour: Optional[np.ndarray] = None
    error: Optional[str] = None


def preprocess_image(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Preprocess image for garment detection.

    Returns:
        Tuple of (grayscale, edges)
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection using Canny
    edges = cv2.Canny(blurred, 30, 100)

    # Dilate edges to connect broken lines
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=2)
    edges = cv2.erode(edges, kernel, iterations=1)

    return gray, edges


def find_garment_contour(edges: np.ndarray, image_shape: Tuple[int, int]) -> Optional[np.ndarray]:
    """
    Find the main garment contour from edge image.

    Returns the largest contour that's likely the garment.
    """
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Filter contours by area (garment should be significant portion of image)
    image_area = image_shape[0] * image_shape[1]
    min_area = image_area * 0.05  # At least 5% of image
    max_area = image_area * 0.95  # At most 95% of image

    valid_contours = [
        c for c in contours
        if min_area < cv2.contourArea(c) < max_area
    ]

    if not valid_contours:
        # Fall back to largest contour
        return max(contours, key=cv2.contourArea)

    # Return largest valid contour
    return max(valid_contours, key=cv2.contourArea)


def classify_garment_type(contour: np.ndarray, image_shape: Tuple[int, int]) -> GarmentType:
    """
    Classify the garment type based on contour shape.

    Uses aspect ratio and shape analysis.
    """
    # Get bounding rectangle
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = h / w if w > 0 else 0

    # Get convex hull and analyze shape
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    contour_area = cv2.contourArea(contour)
    solidity = contour_area / hull_area if hull_area > 0 else 0

    # Pants typically:
    # - Taller than wide (aspect ratio > 1)
    # - Have a concave region at crotch (lower solidity)
    # - Have two "legs" visible at bottom

    if aspect_ratio > 0.8 and solidity < 0.85:
        # Check for pants-like shape (crotch indentation)
        # Look for concave region in lower-middle area
        return GarmentType.PANTS
    elif aspect_ratio < 0.8 and solidity > 0.7:
        # Wider than tall, fairly solid - likely shirt
        return GarmentType.SHIRT
    elif aspect_ratio > 1.2 and solidity > 0.8:
        # Very tall, solid shape - might be dress
        return GarmentType.DRESS

    return GarmentType.UNKNOWN


def detect_pants_keypoints(
    contour: np.ndarray,
    image_shape: Tuple[int, int]
) -> List[Keypoint]:
    """
    Detect keypoints specific to pants/jeans/leggings.

    Key points detected:
    - waist_left, waist_center, waist_right (top edge)
    - crotch_point (where legs meet)
    - left_hem, right_hem (bottom of legs)
    - left_inseam_top, right_inseam_top (inner leg at crotch)
    """
    keypoints = []

    # Get bounding box
    x, y, w, h = cv2.boundingRect(contour)

    # Approximate contour to reduce points
    epsilon = 0.01 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    points = approx.reshape(-1, 2)

    # Sort points by y-coordinate (top to bottom)
    sorted_by_y = points[np.argsort(points[:, 1])]

    # WAISTBAND (top edge)
    # Find points in the top 15% of the contour
    top_threshold = y + h * 0.15
    top_points = points[points[:, 1] < top_threshold]

    if len(top_points) >= 2:
        # Leftmost and rightmost top points
        left_top = top_points[np.argmin(top_points[:, 0])]
        right_top = top_points[np.argmax(top_points[:, 0])]
        center_top = [(left_top[0] + right_top[0]) / 2, (left_top[1] + right_top[1]) / 2]

        keypoints.append(Keypoint("waist_left", float(left_top[0]), float(left_top[1])))
        keypoints.append(Keypoint("waist_right", float(right_top[0]), float(right_top[1])))
        keypoints.append(Keypoint("waist_center", float(center_top[0]), float(center_top[1])))

    # HEM (bottom edge)
    # Find points in the bottom 15% of the contour
    bottom_threshold = y + h * 0.85
    bottom_points = points[points[:, 1] > bottom_threshold]

    if len(bottom_points) >= 2:
        # For pants, we expect two separate leg bottoms
        # Split by x-coordinate (left leg vs right leg)
        center_x = x + w / 2
        left_bottom = bottom_points[bottom_points[:, 0] < center_x]
        right_bottom = bottom_points[bottom_points[:, 0] >= center_x]

        if len(left_bottom) > 0:
            # Find bottommost point of left leg
            left_hem = left_bottom[np.argmax(left_bottom[:, 1])]
            keypoints.append(Keypoint("left_hem", float(left_hem[0]), float(left_hem[1])))

        if len(right_bottom) > 0:
            # Find bottommost point of right leg
            right_hem = right_bottom[np.argmax(right_bottom[:, 1])]
            keypoints.append(Keypoint("right_hem", float(right_hem[0]), float(right_hem[1])))

    # CROTCH POINT (where legs meet)
    # Look for the highest point in the center region
    # This is typically a concave indentation
    center_region_x = (x + w * 0.35, x + w * 0.65)
    center_points = points[
        (points[:, 0] > center_region_x[0]) &
        (points[:, 0] < center_region_x[1])
    ]

    if len(center_points) > 0:
        # Find the point that's highest (smallest y) in the lower half
        lower_half = center_points[center_points[:, 1] > y + h * 0.3]
        if len(lower_half) > 0:
            # The crotch is the topmost point in the lower-center region
            crotch = lower_half[np.argmin(lower_half[:, 1])]
            keypoints.append(Keypoint("crotch_point", float(crotch[0]), float(crotch[1])))

    # INSEAM POINTS (inner leg edges)
    # Left inseam: rightmost point of left leg's inner edge
    # Right inseam: leftmost point of right leg's inner edge
    mid_y = y + h * 0.5

    # Left leg inner edge (look for rightmost points on left side)
    left_leg_points = points[points[:, 0] < center_x]
    left_mid_points = left_leg_points[left_leg_points[:, 1] > mid_y]
    if len(left_mid_points) > 0:
        left_inseam = left_mid_points[np.argmax(left_mid_points[:, 0])]
        keypoints.append(Keypoint("left_inseam", float(left_inseam[0]), float(left_inseam[1])))

    # Right leg inner edge
    right_leg_points = points[points[:, 0] >= center_x]
    right_mid_points = right_leg_points[right_leg_points[:, 1] > mid_y]
    if len(right_mid_points) > 0:
        right_inseam = right_mid_points[np.argmin(right_mid_points[:, 0])]
        keypoints.append(Keypoint("right_inseam", float(right_inseam[0]), float(right_inseam[1])))

    # OUTSEAM POINTS (outer leg edges)
    # Find leftmost point of left leg, rightmost point of right leg
    if len(left_leg_points) > 0:
        left_outer_points = left_leg_points[left_leg_points[:, 1] > y + h * 0.3]
        if len(left_outer_points) > 0:
            left_outseam = left_outer_points[np.argmin(left_outer_points[:, 0])]
            keypoints.append(Keypoint("left_outseam", float(left_outseam[0]), float(left_outseam[1])))

    if len(right_leg_points) > 0:
        right_outer_points = right_leg_points[right_leg_points[:, 1] > y + h * 0.3]
        if len(right_outer_points) > 0:
            right_outseam = right_outer_points[np.argmax(right_outer_points[:, 0])]
            keypoints.append(Keypoint("right_outseam", float(right_outseam[0]), float(right_outseam[1])))

    return keypoints


def calculate_measurements(
    keypoints: List[Keypoint],
    scale_ppcm: Optional[float] = None
) -> Dict[str, float]:
    """
    Calculate garment measurements from detected keypoints.

    Args:
        keypoints: List of detected keypoints
        scale_ppcm: Pixels per centimeter (if known)

    Returns:
        Dict of measurement name -> value in cm (or pixels if no scale)
    """
    measurements = {}

    # Create lookup dict
    kp_dict = {kp.name: (kp.x, kp.y) for kp in keypoints}

    def distance(p1_name: str, p2_name: str) -> Optional[float]:
        if p1_name not in kp_dict or p2_name not in kp_dict:
            return None
        p1, p2 = kp_dict[p1_name], kp_dict[p2_name]
        dist_px = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        if scale_ppcm:
            return dist_px / scale_ppcm  # Convert to cm
        return dist_px

    # WAIST (flat measurement - multiply by 2 for circumference)
    waist = distance("waist_left", "waist_right")
    if waist:
        measurements["waist_flat"] = round(waist, 2)
        measurements["waist_circumference"] = round(waist * 2, 2)

    # INSEAM (crotch to hem)
    # Average of left and right legs
    left_inseam = distance("crotch_point", "left_hem")
    right_inseam = distance("crotch_point", "right_hem")
    if left_inseam and right_inseam:
        measurements["inseam"] = round((left_inseam + right_inseam) / 2, 2)
    elif left_inseam:
        measurements["inseam"] = round(left_inseam, 2)
    elif right_inseam:
        measurements["inseam"] = round(right_inseam, 2)

    # OUTSEAM (waist to hem on outer edge)
    # We need to calculate along the outer edge
    left_outseam = distance("waist_left", "left_hem")
    right_outseam = distance("waist_right", "right_hem")
    if left_outseam and right_outseam:
        measurements["outseam"] = round((left_outseam + right_outseam) / 2, 2)
    elif left_outseam:
        measurements["outseam"] = round(left_outseam, 2)
    elif right_outseam:
        measurements["outseam"] = round(right_outseam, 2)

    # RISE (waist center to crotch)
    rise = distance("waist_center", "crotch_point")
    if rise:
        measurements["rise"] = round(rise, 2)

    # HEM WIDTH (bottom of leg opening)
    # This is trickier - we'd need the width at the hem
    # For now, estimate from left/right hem positions
    if "left_hem" in kp_dict and "right_hem" in kp_dict:
        # This isn't quite right for hem width, but gives an idea
        pass

    return measurements


def detect_garment(
    image: np.ndarray,
    garment_type: Optional[str] = None,
    scale_ppcm: Optional[float] = None
) -> DetectionResult:
    """
    Main function to detect garment keypoints and calculate measurements.

    Args:
        image: BGR image as numpy array
        garment_type: Optional hint ("pants", "shirt", etc.)
        scale_ppcm: Pixels per centimeter for real measurements

    Returns:
        DetectionResult with keypoints and measurements
    """
    try:
        # Preprocess
        gray, edges = preprocess_image(image)

        # Find garment contour
        contour = find_garment_contour(edges, image.shape[:2])

        if contour is None:
            return DetectionResult(
                success=False,
                garment_type=GarmentType.UNKNOWN,
                keypoints=[],
                measurements={},
                error="Could not detect garment outline. Make sure the garment is clearly visible against the background."
            )

        # Classify garment type if not provided
        if garment_type:
            detected_type = GarmentType(garment_type.lower())
        else:
            detected_type = classify_garment_type(contour, image.shape[:2])

        # Detect keypoints based on garment type
        if detected_type == GarmentType.PANTS:
            keypoints = detect_pants_keypoints(contour, image.shape[:2])
        else:
            # Default to pants detection for now
            keypoints = detect_pants_keypoints(contour, image.shape[:2])

        if not keypoints:
            return DetectionResult(
                success=False,
                garment_type=detected_type,
                keypoints=[],
                measurements={},
                contour=contour,
                error="Could not detect keypoints. Try adjusting the garment position or lighting."
            )

        # Calculate measurements
        measurements = calculate_measurements(keypoints, scale_ppcm)

        return DetectionResult(
            success=True,
            garment_type=detected_type,
            keypoints=keypoints,
            measurements=measurements,
            contour=contour
        )

    except Exception as e:
        return DetectionResult(
            success=False,
            garment_type=GarmentType.UNKNOWN,
            keypoints=[],
            measurements={},
            error=str(e)
        )


def draw_keypoints_on_image(
    image: np.ndarray,
    keypoints: List[Keypoint],
    contour: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Draw detected keypoints and contour on image for visualization.
    """
    output = image.copy()

    # Draw contour
    if contour is not None:
        cv2.drawContours(output, [contour], -1, (0, 255, 0), 2)

    # Draw keypoints
    colors = {
        "waist": (255, 0, 0),      # Blue
        "crotch": (0, 0, 255),     # Red
        "hem": (0, 255, 255),      # Yellow
        "inseam": (255, 0, 255),   # Magenta
        "outseam": (255, 255, 0),  # Cyan
    }

    for kp in keypoints:
        # Determine color based on keypoint name
        color = (0, 255, 0)  # Default green
        for key, c in colors.items():
            if key in kp.name:
                color = c
                break

        # Draw point
        center = (int(kp.x), int(kp.y))
        cv2.circle(output, center, 8, color, -1)
        cv2.circle(output, center, 10, (255, 255, 255), 2)

        # Draw label
        cv2.putText(
            output,
            kp.name,
            (center[0] + 12, center[1] + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

    return output


# Convenience function for API
def detect_from_bytes(
    image_bytes: bytes,
    garment_type: Optional[str] = None,
    scale_ppcm: Optional[float] = None
) -> Dict:
    """
    Detect garment from image bytes (for API use).

    Returns dict suitable for JSON response.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        return {"success": False, "error": "Failed to decode image"}

    result = detect_garment(image, garment_type, scale_ppcm)

    # Convert to JSON-serializable dict
    return {
        "success": result.success,
        "garment_type": result.garment_type.value,
        "keypoints": [
            {"name": kp.name, "x": kp.x, "y": kp.y, "confidence": kp.confidence}
            for kp in result.keypoints
        ],
        "measurements": result.measurements,
        "error": result.error
    }


if __name__ == "__main__":
    # Test with a sample image
    import sys

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        image = cv2.imread(image_path)

        if image is None:
            print(f"Could not load image: {image_path}")
            sys.exit(1)

        # Test detection
        result = detect_garment(image, scale_ppcm=10.0)  # Assume 10 px/cm for testing

        print(f"Success: {result.success}")
        print(f"Garment type: {result.garment_type.value}")
        print(f"Keypoints detected: {len(result.keypoints)}")
        for kp in result.keypoints:
            print(f"  - {kp.name}: ({kp.x:.1f}, {kp.y:.1f})")
        print(f"Measurements: {result.measurements}")

        if result.error:
            print(f"Error: {result.error}")

        # Save visualization
        if result.success:
            vis = draw_keypoints_on_image(image, result.keypoints, result.contour)
            cv2.imwrite("detection_result.jpg", vis)
            print("Saved visualization to detection_result.jpg")
    else:
        print("Usage: python garment_detector.py <image_path>")
