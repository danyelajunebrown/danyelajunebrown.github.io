"""
ArUco Marker Calibration Module

Detects ArUco markers in images and calculates the scale factor
(pixels per centimeter) for accurate real-world measurements.
"""

import cv2
import numpy as np
from cv2 import aruco
from typing import Tuple, Dict, List, Optional
import io
from PIL import Image


# Default marker size in centimeters (5cm x 5cm markers)
DEFAULT_MARKER_SIZE_CM = 5.0

# ArUco dictionary - using 4x4 with 50 markers (simple, robust)
ARUCO_DICT = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)


def detect_aruco_markers(image: np.ndarray) -> Tuple[List, Optional[np.ndarray], List]:
    """
    Detect ArUco markers in an image.

    Args:
        image: BGR image as numpy array

    Returns:
        Tuple of (corners, ids, rejected)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    parameters = aruco.DetectorParameters()
    # Tune for better detection
    parameters.adaptiveThreshWinSizeMin = 3
    parameters.adaptiveThreshWinSizeMax = 23
    parameters.adaptiveThreshWinSizeStep = 10
    parameters.minMarkerPerimeterRate = 0.02
    parameters.maxMarkerPerimeterRate = 4.0

    detector = aruco.ArucoDetector(ARUCO_DICT, parameters)
    corners, ids, rejected = detector.detectMarkers(gray)

    return corners, ids, rejected


def calculate_scale_from_markers(
    corners: List,
    marker_size_cm: float = DEFAULT_MARKER_SIZE_CM
) -> Tuple[float, float]:
    """
    Calculate scale factor (pixels per cm) from detected ArUco markers.

    Args:
        corners: List of marker corners from detectMarkers
        marker_size_cm: Physical size of marker side in centimeters

    Returns:
        Tuple of (pixels_per_cm, confidence)
        Confidence is 0-1 based on consistency of measurements
    """
    if not corners or len(corners) == 0:
        raise ValueError("No markers detected")

    marker_sizes_px = []

    for corner in corners:
        # Corner shape is (1, 4, 2) - 4 corners with x,y coordinates
        pts = corner[0]

        # Calculate all 4 side lengths
        side_lengths = [
            np.linalg.norm(pts[i] - pts[(i+1) % 4])
            for i in range(4)
        ]

        # Average side length for this marker
        avg_side = np.mean(side_lengths)
        marker_sizes_px.append(avg_side)

        # Check if marker is roughly square (confidence indicator)
        side_std = np.std(side_lengths)
        if side_std / avg_side > 0.1:  # More than 10% variation
            # Marker might be at an angle or distorted
            pass

    # Average across all detected markers
    avg_marker_px = np.mean(marker_sizes_px)

    # Calculate pixels per centimeter
    pixels_per_cm = avg_marker_px / marker_size_cm

    # Calculate confidence based on consistency across markers
    if len(marker_sizes_px) > 1:
        consistency = 1.0 - (np.std(marker_sizes_px) / avg_marker_px)
        confidence = max(0.0, min(1.0, consistency))
    else:
        confidence = 0.8  # Single marker, decent confidence

    return pixels_per_cm, confidence


def calibrate_from_image(
    image_path: str = None,
    image_bytes: bytes = None,
    marker_size_cm: float = DEFAULT_MARKER_SIZE_CM
) -> Dict:
    """
    Full calibration pipeline: load image, detect markers, calculate scale.

    Args:
        image_path: Path to image file (optional if image_bytes provided)
        image_bytes: Raw image bytes (optional if image_path provided)
        marker_size_cm: Physical size of marker in cm

    Returns:
        Dict with calibration results:
        {
            'success': bool,
            'scale_ppcm': float (pixels per cm),
            'scale_ppi': float (pixels per inch),
            'markers_detected': int,
            'marker_ids': list,
            'confidence': float (0-1),
            'error': str (if failed)
        }
    """
    try:
        # Load image
        if image_bytes:
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif image_path:
            image = cv2.imread(image_path)
        else:
            return {'success': False, 'error': 'No image provided'}

        if image is None:
            return {'success': False, 'error': 'Failed to load image'}

        # Detect markers
        corners, ids, rejected = detect_aruco_markers(image)

        if ids is None or len(ids) == 0:
            return {
                'success': False,
                'error': 'No ArUco markers detected. Make sure the calibration card is visible and well-lit.',
                'markers_detected': 0
            }

        # Calculate scale
        pixels_per_cm, confidence = calculate_scale_from_markers(corners, marker_size_cm)

        return {
            'success': True,
            'scale_ppcm': round(pixels_per_cm, 2),
            'scale_ppi': round(pixels_per_cm * 2.54, 2),
            'markers_detected': len(ids),
            'marker_ids': ids.flatten().tolist(),
            'confidence': round(confidence, 2)
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def draw_detected_markers(
    image: np.ndarray,
    corners: List,
    ids: np.ndarray
) -> np.ndarray:
    """
    Draw detected markers on image for visualization.

    Args:
        image: BGR image
        corners: Detected corner points
        ids: Marker IDs

    Returns:
        Image with markers drawn
    """
    output = image.copy()

    if ids is not None and len(ids) > 0:
        aruco.drawDetectedMarkers(output, corners, ids)

        # Add ID labels
        for i, corner in enumerate(corners):
            center = corner[0].mean(axis=0).astype(int)
            cv2.putText(
                output,
                f"ID:{ids[i][0]}",
                (center[0] - 20, center[1] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    return output


def generate_aruco_card_svg(
    marker_ids: List[int] = [0, 1, 2, 3],
    marker_size_cm: float = 5.0,
    margin_cm: float = 1.0
) -> str:
    """
    Generate SVG for printable ArUco calibration card.

    Args:
        marker_ids: List of marker IDs to include (default: 0-3)
        marker_size_cm: Size of each marker in cm
        margin_cm: Margin between markers in cm

    Returns:
        SVG string
    """
    # SVG dimensions (A4-ish, but works for letter too)
    # 2x2 grid of markers
    card_width_cm = (marker_size_cm * 2) + (margin_cm * 3)
    card_height_cm = (marker_size_cm * 2) + (margin_cm * 3)

    # Convert to pixels at 96 DPI for SVG
    dpi = 96
    cm_to_px = dpi / 2.54

    card_width_px = card_width_cm * cm_to_px
    card_height_px = card_height_cm * cm_to_px
    marker_size_px = marker_size_cm * cm_to_px
    margin_px = margin_cm * cm_to_px

    svg_parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{card_width_px:.0f}" height="{card_height_px:.0f}" viewBox="0 0 {card_width_px:.0f} {card_height_px:.0f}">',
        f'  <rect width="100%" height="100%" fill="white"/>',
        f'  <text x="{card_width_px/2}" y="20" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">',
        f'    Make It Cunt - Calibration Card (Markers are {marker_size_cm}cm x {marker_size_cm}cm)',
        f'  </text>',
    ]

    # Generate 4 markers in 2x2 grid
    positions = [
        (margin_px, margin_px + 30),  # Top-left
        (margin_px + marker_size_px + margin_px, margin_px + 30),  # Top-right
        (margin_px, margin_px + marker_size_px + margin_px + 30),  # Bottom-left
        (margin_px + marker_size_px + margin_px, margin_px + marker_size_px + margin_px + 30),  # Bottom-right
    ]

    for idx, (x, y) in enumerate(positions):
        if idx < len(marker_ids):
            marker_id = marker_ids[idx]
            marker_svg = _generate_single_aruco_svg(marker_id, x, y, marker_size_px)
            svg_parts.append(marker_svg)

    # Add instructions at bottom
    svg_parts.extend([
        f'  <text x="{card_width_px/2}" y="{card_height_px - 30}" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">',
        f'    Print at 100% scale. Place next to garment when photographing.',
        f'  </text>',
        f'  <text x="{card_width_px/2}" y="{card_height_px - 15}" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">',
        f'    Each marker is exactly {marker_size_cm}cm x {marker_size_cm}cm',
        f'  </text>',
        '</svg>'
    ])

    return '\n'.join(svg_parts)


def _generate_single_aruco_svg(marker_id: int, x: float, y: float, size: float) -> str:
    """
    Generate SVG for a single ArUco marker.

    Uses DICT_4X4_50 encoding.
    """
    # Generate the marker using OpenCV
    marker_img = aruco.generateImageMarker(ARUCO_DICT, marker_id, 100)

    # Convert to SVG rectangles
    cell_size = size / 6  # 4x4 data + 1 border on each side = 6 cells

    svg_parts = [f'  <g transform="translate({x},{y})">']

    # The marker is 6x6 including border
    for row in range(6):
        for col in range(6):
            # Map to the 100x100 image
            img_row = int((row + 0.5) * 100 / 6)
            img_col = int((col + 0.5) * 100 / 6)

            # Check if this cell should be black
            if marker_img[img_row, img_col] < 128:
                rect_x = col * cell_size
                rect_y = row * cell_size
                svg_parts.append(
                    f'    <rect x="{rect_x:.1f}" y="{rect_y:.1f}" '
                    f'width="{cell_size:.1f}" height="{cell_size:.1f}" fill="black"/>'
                )

    svg_parts.append('  </g>')
    return '\n'.join(svg_parts)


if __name__ == '__main__':
    # Test: Generate calibration card
    svg = generate_aruco_card_svg()
    with open('aruco-card.svg', 'w') as f:
        f.write(svg)
    print("Generated aruco-card.svg")
