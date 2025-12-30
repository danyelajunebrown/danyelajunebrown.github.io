"""
Body Model Module - Make It Cunt v3.0

Detects anatomical landmarks on body mesh and extracts measurements.
Generates movement envelope for dynamic ease calculation.

Dependencies: numpy, scipy, trimesh (optional)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from scipy import ndimage
from scipy.spatial import ConvexHull
from scipy.signal import find_peaks

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False


class BodyLandmark(Enum):
    """Key anatomical landmarks for garment fitting"""
    # Head/Neck
    TOP_OF_HEAD = "top_of_head"
    NECK_BASE = "neck_base"

    # Shoulders
    LEFT_SHOULDER = "left_shoulder"
    RIGHT_SHOULDER = "right_shoulder"
    SHOULDER_CENTER = "shoulder_center"

    # Torso
    BUST_APEX_LEFT = "bust_apex_left"
    BUST_APEX_RIGHT = "bust_apex_right"
    UNDERBUST = "underbust"
    WAIST = "waist"
    HIGH_HIP = "high_hip"
    HIP = "hip"

    # Lower body
    CROTCH = "crotch"
    LEFT_KNEE = "left_knee"
    RIGHT_KNEE = "right_knee"
    LEFT_ANKLE = "left_ankle"
    RIGHT_ANKLE = "right_ankle"

    # Arms
    LEFT_ELBOW = "left_elbow"
    RIGHT_ELBOW = "right_elbow"
    LEFT_WRIST = "left_wrist"
    RIGHT_WRIST = "right_wrist"


@dataclass
class CrossSection:
    """A horizontal cross-section through the body mesh"""
    height: float  # Y coordinate
    points: np.ndarray  # 2D points (X, Z) on the contour
    circumference: float  # Perimeter of the cross-section
    center: np.ndarray  # Center point (X, Z)
    width: float  # Max width (X direction)
    depth: float  # Max depth (Z direction)
    area: float  # Cross-sectional area

    def to_dict(self) -> Dict[str, Any]:
        return {
            'height': float(self.height),
            'circumference': float(self.circumference),
            'center': self.center.tolist(),
            'width': float(self.width),
            'depth': float(self.depth),
            'area': float(self.area)
        }


@dataclass
class BodyMeasurements:
    """Extracted body measurements from 3D scan"""
    # Heights (from floor)
    total_height: float = 0.0
    shoulder_height: float = 0.0
    bust_height: float = 0.0
    waist_height: float = 0.0
    hip_height: float = 0.0
    crotch_height: float = 0.0
    knee_height: float = 0.0
    ankle_height: float = 0.0

    # Circumferences
    neck_circumference: float = 0.0
    shoulder_circumference: float = 0.0
    bust_circumference: float = 0.0
    underbust_circumference: float = 0.0
    waist_circumference: float = 0.0
    high_hip_circumference: float = 0.0
    hip_circumference: float = 0.0
    thigh_circumference: float = 0.0
    knee_circumference: float = 0.0
    calf_circumference: float = 0.0
    ankle_circumference: float = 0.0

    # Widths
    shoulder_width: float = 0.0
    bust_width: float = 0.0
    waist_width: float = 0.0
    hip_width: float = 0.0

    # Lengths
    torso_length: float = 0.0  # Shoulder to waist
    front_rise: float = 0.0  # Waist to crotch (front)
    back_rise: float = 0.0  # Waist to crotch (back)
    inseam: float = 0.0  # Crotch to ankle
    outseam: float = 0.0  # Waist to ankle
    arm_length: float = 0.0  # Shoulder to wrist

    # Unit (for reference)
    unit: str = "mm"

    def to_dict(self) -> Dict[str, float]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


@dataclass
class MovementEnvelope:
    """
    Expanded body envelope for movement ease.

    Different activities require different amounts of ease at different body points.
    This envelope represents the space the body needs to move freely.
    """
    base_mesh_vertices: np.ndarray
    expanded_vertices: np.ndarray
    ease_map: Dict[str, float]  # Landmark -> ease amount in mm

    @staticmethod
    def default_ease() -> Dict[str, float]:
        """Default ease values for active movement"""
        return {
            'shoulder': 50.0,  # mm - for arm movement
            'bust': 30.0,
            'waist': 20.0,
            'hip': 40.0,
            'crotch': 60.0,  # More ease for leg movement
            'knee': 50.0,
            'elbow': 40.0,
        }

    @staticmethod
    def wild_movement_ease() -> Dict[str, float]:
        """Extra ease for wild/dance movement - user's requirement"""
        return {
            'shoulder': 80.0,  # mm - lots of arm swinging
            'bust': 50.0,
            'waist': 40.0,
            'hip': 70.0,
            'crotch': 100.0,  # Splits, high kicks
            'knee': 80.0,
            'elbow': 60.0,
        }


class BodyModel:
    """
    Analyzes a 3D body scan to extract landmarks and measurements.

    The key insight: body landmarks can be detected by analyzing
    cross-sections at different heights and finding characteristic
    shapes and size changes.
    """

    def __init__(self, vertices: np.ndarray, faces: np.ndarray):
        """
        Initialize with mesh data.

        Args:
            vertices: Nx3 array of vertex positions (Y-up, centered at origin)
            faces: Mx3 array of face indices
        """
        self.vertices = vertices
        self.faces = faces

        # Mesh bounds
        self.min_y = vertices[:, 1].min()
        self.max_y = vertices[:, 1].max()
        self.height = self.max_y - self.min_y

        # Storage
        self.landmarks: Dict[BodyLandmark, np.ndarray] = {}
        self.cross_sections: Dict[float, CrossSection] = {}
        self.measurements = BodyMeasurements()

    def analyze(self, num_sections: int = 100) -> 'BodyModel':
        """
        Full analysis pipeline.

        1. Generate cross-sections at regular height intervals
        2. Detect landmarks from cross-section patterns
        3. Extract measurements
        """
        self._generate_cross_sections(num_sections)
        self._detect_landmarks()
        self._extract_measurements()
        return self

    def _generate_cross_sections(self, num_sections: int):
        """
        Generate horizontal cross-sections through the body.

        For each height, find all vertices near that height,
        project to 2D (X, Z), and compute the convex hull.
        """
        heights = np.linspace(self.min_y + 1, self.max_y - 1, num_sections)
        slice_thickness = (self.max_y - self.min_y) / num_sections

        for height in heights:
            # Find vertices near this height
            mask = np.abs(self.vertices[:, 1] - height) < slice_thickness
            if mask.sum() < 10:
                continue

            points_2d = self.vertices[mask][:, [0, 2]]  # X, Z only

            try:
                # Compute convex hull for circumference
                hull = ConvexHull(points_2d)
                hull_points = points_2d[hull.vertices]

                # Compute metrics
                circumference = hull.area  # In 2D, "area" is perimeter
                center = hull_points.mean(axis=0)
                width = points_2d[:, 0].max() - points_2d[:, 0].min()
                depth = points_2d[:, 1].max() - points_2d[:, 1].min()

                # Approximate area using hull
                area = self._polygon_area(hull_points)

                self.cross_sections[height] = CrossSection(
                    height=height,
                    points=hull_points,
                    circumference=circumference,
                    center=center,
                    width=width,
                    depth=depth,
                    area=area
                )
            except Exception:
                # Skip problematic cross-sections
                continue

    def _polygon_area(self, points: np.ndarray) -> float:
        """Compute area of a 2D polygon using shoelace formula"""
        n = len(points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i, 0] * points[j, 1]
            area -= points[j, 0] * points[i, 1]
        return abs(area) / 2.0

    def _detect_landmarks(self):
        """
        Detect anatomical landmarks by analyzing cross-section patterns.

        Key observations:
        - Waist: Local minimum in circumference
        - Hip: Local maximum below waist
        - Bust: Local maximum above waist
        - Crotch: Where body splits into two legs (circumference drops sharply)
        - Shoulders: Widest point in upper body
        """
        if not self.cross_sections:
            return

        heights = sorted(self.cross_sections.keys())
        circumferences = [self.cross_sections[h].circumference for h in heights]
        widths = [self.cross_sections[h].width for h in heights]

        heights = np.array(heights)
        circumferences = np.array(circumferences)
        widths = np.array(widths)

        # Smooth the signals for better peak detection
        from scipy.ndimage import gaussian_filter1d
        circ_smooth = gaussian_filter1d(circumferences, sigma=3)
        width_smooth = gaussian_filter1d(widths, sigma=3)

        # Find waist (minimum circumference in middle third of body)
        middle_start = int(len(heights) * 0.3)
        middle_end = int(len(heights) * 0.6)
        middle_circ = circ_smooth[middle_start:middle_end]
        waist_idx = middle_start + np.argmin(middle_circ)
        waist_height = heights[waist_idx]

        self.landmarks[BodyLandmark.WAIST] = np.array([
            self.cross_sections[waist_height].center[0],
            waist_height,
            self.cross_sections[waist_height].center[1]
        ])

        # Find hip (maximum circumference below waist)
        below_waist = circ_smooth[:waist_idx]
        if len(below_waist) > 5:
            hip_idx = np.argmax(below_waist)
            hip_height = heights[hip_idx]
            self.landmarks[BodyLandmark.HIP] = np.array([
                self.cross_sections[hip_height].center[0],
                hip_height,
                self.cross_sections[hip_height].center[1]
            ])

        # Find bust (maximum circumference above waist, below shoulders)
        above_waist_end = int(len(heights) * 0.85)  # Stop before shoulders
        above_waist = circ_smooth[waist_idx:above_waist_end]
        if len(above_waist) > 5:
            bust_idx = waist_idx + np.argmax(above_waist)
            bust_height = heights[bust_idx]
            cs = self.cross_sections[bust_height]

            # Bust apexes are the widest points
            self.landmarks[BodyLandmark.BUST_APEX_LEFT] = np.array([
                cs.center[0] - cs.width / 4,
                bust_height,
                cs.center[1]
            ])
            self.landmarks[BodyLandmark.BUST_APEX_RIGHT] = np.array([
                cs.center[0] + cs.width / 4,
                bust_height,
                cs.center[1]
            ])

        # Find shoulders (widest point in upper body)
        upper_start = int(len(heights) * 0.75)
        upper_width = width_smooth[upper_start:]
        if len(upper_width) > 3:
            shoulder_idx = upper_start + np.argmax(upper_width)
            shoulder_height = heights[shoulder_idx]
            cs = self.cross_sections[shoulder_height]

            self.landmarks[BodyLandmark.LEFT_SHOULDER] = np.array([
                cs.center[0] - cs.width / 2,
                shoulder_height,
                cs.center[1]
            ])
            self.landmarks[BodyLandmark.RIGHT_SHOULDER] = np.array([
                cs.center[0] + cs.width / 2,
                shoulder_height,
                cs.center[1]
            ])
            self.landmarks[BodyLandmark.SHOULDER_CENTER] = np.array([
                cs.center[0],
                shoulder_height,
                cs.center[1]
            ])

        # Find crotch (sharp drop in circumference below hip)
        if BodyLandmark.HIP in self.landmarks:
            hip_height = self.landmarks[BodyLandmark.HIP][1]
            hip_idx = np.searchsorted(heights, hip_height)

            # Look for where circumference drops significantly
            below_hip = circ_smooth[:hip_idx]
            if len(below_hip) > 10:
                # Find where circumference drops to ~50-60% of hip
                hip_circ = circ_smooth[hip_idx]
                threshold = hip_circ * 0.6

                for i in range(hip_idx - 1, -1, -1):
                    if circ_smooth[i] < threshold:
                        crotch_height = heights[i + 2]  # Slightly above the drop
                        self.landmarks[BodyLandmark.CROTCH] = np.array([
                            self.cross_sections[crotch_height].center[0],
                            crotch_height,
                            self.cross_sections[crotch_height].center[1]
                        ])
                        break

        # Find knees (local minimum in leg circumference)
        if BodyLandmark.CROTCH in self.landmarks:
            crotch_height = self.landmarks[BodyLandmark.CROTCH][1]
            crotch_idx = np.searchsorted(heights, crotch_height)

            # Knee is roughly 40-50% down the leg
            leg_length = crotch_height - heights[0]
            knee_height_approx = heights[0] + leg_length * 0.45

            knee_idx = np.searchsorted(heights, knee_height_approx)
            if knee_idx > 0 and knee_idx < len(heights):
                knee_height = heights[knee_idx]
                self.landmarks[BodyLandmark.LEFT_KNEE] = np.array([
                    -self.cross_sections[knee_height].width / 4,
                    knee_height,
                    0
                ])
                self.landmarks[BodyLandmark.RIGHT_KNEE] = np.array([
                    self.cross_sections[knee_height].width / 4,
                    knee_height,
                    0
                ])

        # Find ankles (bottom of mesh)
        ankle_height = heights[2]  # A bit above the floor
        if ankle_height in self.cross_sections:
            cs = self.cross_sections[ankle_height]
            self.landmarks[BodyLandmark.LEFT_ANKLE] = np.array([
                -cs.width / 4, ankle_height, 0
            ])
            self.landmarks[BodyLandmark.RIGHT_ANKLE] = np.array([
                cs.width / 4, ankle_height, 0
            ])

        # Top of head
        self.landmarks[BodyLandmark.TOP_OF_HEAD] = np.array([
            0, self.max_y, 0
        ])

    def _extract_measurements(self):
        """Extract body measurements from landmarks and cross-sections"""
        heights = sorted(self.cross_sections.keys())

        # Total height
        self.measurements.total_height = self.height

        # Heights from landmarks
        if BodyLandmark.SHOULDER_CENTER in self.landmarks:
            self.measurements.shoulder_height = self.landmarks[BodyLandmark.SHOULDER_CENTER][1] - self.min_y

        if BodyLandmark.WAIST in self.landmarks:
            self.measurements.waist_height = self.landmarks[BodyLandmark.WAIST][1] - self.min_y

        if BodyLandmark.HIP in self.landmarks:
            self.measurements.hip_height = self.landmarks[BodyLandmark.HIP][1] - self.min_y

        if BodyLandmark.CROTCH in self.landmarks:
            self.measurements.crotch_height = self.landmarks[BodyLandmark.CROTCH][1] - self.min_y

        # Circumferences at key heights
        def get_circ_at_landmark(landmark: BodyLandmark) -> float:
            if landmark not in self.landmarks:
                return 0.0
            height = self.landmarks[landmark][1]
            # Find closest cross-section
            closest = min(heights, key=lambda h: abs(h - height))
            return self.cross_sections[closest].circumference

        if BodyLandmark.WAIST in self.landmarks:
            self.measurements.waist_circumference = get_circ_at_landmark(BodyLandmark.WAIST)
            self.measurements.waist_width = self.cross_sections[
                self.landmarks[BodyLandmark.WAIST][1]
            ].width if self.landmarks[BodyLandmark.WAIST][1] in self.cross_sections else 0

        if BodyLandmark.HIP in self.landmarks:
            self.measurements.hip_circumference = get_circ_at_landmark(BodyLandmark.HIP)
            hip_h = self.landmarks[BodyLandmark.HIP][1]
            closest = min(heights, key=lambda h: abs(h - hip_h))
            self.measurements.hip_width = self.cross_sections[closest].width

        if BodyLandmark.BUST_APEX_LEFT in self.landmarks:
            bust_h = self.landmarks[BodyLandmark.BUST_APEX_LEFT][1]
            closest = min(heights, key=lambda h: abs(h - bust_h))
            self.measurements.bust_circumference = self.cross_sections[closest].circumference
            self.measurements.bust_height = bust_h - self.min_y

        # Shoulder width
        if BodyLandmark.LEFT_SHOULDER in self.landmarks and BodyLandmark.RIGHT_SHOULDER in self.landmarks:
            left = self.landmarks[BodyLandmark.LEFT_SHOULDER]
            right = self.landmarks[BodyLandmark.RIGHT_SHOULDER]
            self.measurements.shoulder_width = np.linalg.norm(left - right)

        # Torso length (shoulder to waist)
        if BodyLandmark.SHOULDER_CENTER in self.landmarks and BodyLandmark.WAIST in self.landmarks:
            shoulder = self.landmarks[BodyLandmark.SHOULDER_CENTER][1]
            waist = self.landmarks[BodyLandmark.WAIST][1]
            self.measurements.torso_length = shoulder - waist

        # Rise (waist to crotch)
        if BodyLandmark.WAIST in self.landmarks and BodyLandmark.CROTCH in self.landmarks:
            waist = self.landmarks[BodyLandmark.WAIST][1]
            crotch = self.landmarks[BodyLandmark.CROTCH][1]
            # Front and back rise are approximated as same for now
            self.measurements.front_rise = waist - crotch
            self.measurements.back_rise = waist - crotch

        # Inseam (crotch to ankle)
        if BodyLandmark.CROTCH in self.landmarks and BodyLandmark.LEFT_ANKLE in self.landmarks:
            crotch = self.landmarks[BodyLandmark.CROTCH][1]
            ankle = self.landmarks[BodyLandmark.LEFT_ANKLE][1]
            self.measurements.inseam = crotch - ankle

        # Outseam (waist to ankle)
        if BodyLandmark.WAIST in self.landmarks and BodyLandmark.LEFT_ANKLE in self.landmarks:
            waist = self.landmarks[BodyLandmark.WAIST][1]
            ankle = self.landmarks[BodyLandmark.LEFT_ANKLE][1]
            self.measurements.outseam = waist - ankle

        # Thigh circumference (just below crotch)
        if BodyLandmark.CROTCH in self.landmarks:
            crotch_h = self.landmarks[BodyLandmark.CROTCH][1]
            thigh_h = crotch_h - 50  # 50mm below crotch
            closest = min(heights, key=lambda h: abs(h - thigh_h))
            if closest in self.cross_sections:
                # Divide by 2 for single leg
                self.measurements.thigh_circumference = self.cross_sections[closest].circumference / 2

        # Knee circumference
        if BodyLandmark.LEFT_KNEE in self.landmarks:
            knee_h = self.landmarks[BodyLandmark.LEFT_KNEE][1]
            closest = min(heights, key=lambda h: abs(h - knee_h))
            if closest in self.cross_sections:
                self.measurements.knee_circumference = self.cross_sections[closest].circumference / 2

        # Ankle circumference
        if BodyLandmark.LEFT_ANKLE in self.landmarks:
            ankle_h = self.landmarks[BodyLandmark.LEFT_ANKLE][1]
            closest = min(heights, key=lambda h: abs(h - ankle_h))
            if closest in self.cross_sections:
                self.measurements.ankle_circumference = self.cross_sections[closest].circumference / 2

    def generate_movement_envelope(self,
                                   ease_profile: str = "default") -> MovementEnvelope:
        """
        Generate an expanded mesh representing the space needed for movement.

        Args:
            ease_profile: "default", "wild", or custom dict

        Returns:
            MovementEnvelope with expanded vertices
        """
        if ease_profile == "wild":
            ease_map = MovementEnvelope.wild_movement_ease()
        elif ease_profile == "default":
            ease_map = MovementEnvelope.default_ease()
        else:
            ease_map = MovementEnvelope.default_ease()

        # Create expanded vertices
        expanded = self.vertices.copy()

        # Expand vertices based on their height (which landmark zone they're in)
        for i, v in enumerate(expanded):
            height = v[1]

            # Determine which zone this vertex is in and apply appropriate ease
            ease = 20.0  # Default ease

            if BodyLandmark.SHOULDER_CENTER in self.landmarks:
                if height > self.landmarks[BodyLandmark.SHOULDER_CENTER][1] - 50:
                    ease = ease_map.get('shoulder', 50.0)

            if BodyLandmark.WAIST in self.landmarks:
                waist_h = self.landmarks[BodyLandmark.WAIST][1]
                if abs(height - waist_h) < 100:
                    ease = ease_map.get('waist', 20.0)

            if BodyLandmark.HIP in self.landmarks:
                hip_h = self.landmarks[BodyLandmark.HIP][1]
                if abs(height - hip_h) < 100:
                    ease = ease_map.get('hip', 40.0)

            if BodyLandmark.CROTCH in self.landmarks:
                crotch_h = self.landmarks[BodyLandmark.CROTCH][1]
                if abs(height - crotch_h) < 100:
                    ease = ease_map.get('crotch', 60.0)

            if BodyLandmark.LEFT_KNEE in self.landmarks:
                knee_h = self.landmarks[BodyLandmark.LEFT_KNEE][1]
                if abs(height - knee_h) < 100:
                    ease = ease_map.get('knee', 50.0)

            # Expand outward from center (X and Z directions)
            center_xz = np.array([0, v[2]])  # Assuming centered at X=0
            direction = v[[0, 2]] - center_xz
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
                expanded[i, 0] += direction[0] * ease
                expanded[i, 2] += direction[1] * ease

        return MovementEnvelope(
            base_mesh_vertices=self.vertices,
            expanded_vertices=expanded,
            ease_map=ease_map
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export body model to dictionary for API responses"""
        return {
            'landmarks': {
                lm.value: pos.tolist() for lm, pos in self.landmarks.items()
            },
            'measurements': self.measurements.to_dict(),
            'cross_sections': {
                str(h): cs.to_dict() for h, cs in self.cross_sections.items()
            },
            'bounds': {
                'min_y': float(self.min_y),
                'max_y': float(self.max_y),
                'height': float(self.height)
            }
        }


def analyze_body_mesh(vertices: np.ndarray, faces: np.ndarray,
                      movement_profile: str = "wild") -> Dict[str, Any]:
    """
    Convenience function for API use.

    Args:
        vertices: Nx3 array of vertex positions
        faces: Mx3 array of face indices
        movement_profile: "default" or "wild" for movement ease

    Returns:
        Dict with landmarks, measurements, and movement envelope info
    """
    model = BodyModel(vertices, faces)
    model.analyze()

    envelope = model.generate_movement_envelope(movement_profile)

    result = model.to_dict()
    result['movement_envelope'] = {
        'ease_profile': movement_profile,
        'ease_map': envelope.ease_map
    }

    return result
