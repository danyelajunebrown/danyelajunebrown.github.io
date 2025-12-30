"""
Pattern Generator Module - Make It Cunt v3.0

Generates actual sewing pattern pieces from fit analysis results.
Outputs SVG with seam allowances, notches, grain lines, and instructions.

NOT JUST RECTANGLES - creates shaped pieces that match garment silhouette.

Dependencies: numpy, svgwrite
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import io

try:
    import svgwrite
    SVGWRITE_AVAILABLE = True
except ImportError:
    SVGWRITE_AVAILABLE = False
    print("Warning: svgwrite not installed. Pattern generation will be limited.")

from fit_analysis import FitIssue, ModificationRecommendation, BodyZone
from garment_model import GarmentModel, PatternPiece


class PatternPieceType(Enum):
    """Types of pattern pieces we generate"""
    EXTENSION = "extension"  # Add length
    GUSSET = "gusset"  # Add width/ease
    DART = "dart"  # Remove excess
    INSERT_PANEL = "insert_panel"  # Side panel
    FACING = "facing"  # Finish edge


@dataclass
class Notch:
    """A notch mark on a pattern piece for alignment"""
    position: np.ndarray  # 2D position on pattern
    direction: np.ndarray  # Direction notch points (into seam)
    label: str  # e.g., "A", "1", "match to front"


@dataclass
class GrainLine:
    """Grain line indicator on pattern"""
    start: np.ndarray
    end: np.ndarray
    label: str = "GRAIN"


@dataclass
class GeneratedPattern:
    """A complete pattern piece ready for output"""
    name: str
    piece_type: PatternPieceType
    outline: np.ndarray  # 2D points defining the shape (with seam allowance)
    cut_line: np.ndarray  # Actual cut line (outline)
    stitch_line: np.ndarray  # Sewing line (inside seam allowance)
    seam_allowance: float  # in mm
    notches: List[Notch]
    grain_line: Optional[GrainLine]
    labels: Dict[str, Tuple[np.ndarray, str]]  # position -> text
    instructions: str
    area_mm2: float
    dimensions_mm: Tuple[float, float]  # width, height

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.piece_type.value,
            'seam_allowance_mm': float(self.seam_allowance),
            'notch_count': len(self.notches),
            'has_grain_line': self.grain_line is not None,
            'area_mm2': float(self.area_mm2),
            'dimensions_mm': {
                'width': float(self.dimensions_mm[0]),
                'height': float(self.dimensions_mm[1])
            },
            'instructions': self.instructions
        }


class PatternGenerator:
    """
    Generates pattern pieces for garment modifications.

    Key improvement over v2: generates SHAPED pieces, not rectangles.
    - Extensions taper to match garment silhouette
    - Gussets are diamond/football shaped for proper fit
    - All pieces include seam allowances, notches, grain lines
    """

    # Default seam allowances by fabric type (mm)
    SEAM_ALLOWANCES = {
        'woven': 15,  # Standard 5/8" for woven
        'knit': 10,  # Smaller for stretch
        'denim': 15,
        'default': 12  # ~1/2"
    }

    def __init__(self, fabric_type: str = 'default'):
        self.fabric_type = fabric_type
        self.seam_allowance = self.SEAM_ALLOWANCES.get(fabric_type, 12)

    def generate_from_recommendations(self,
                                       recommendations: List[ModificationRecommendation],
                                       garment: GarmentModel) -> List[GeneratedPattern]:
        """
        Generate pattern pieces from fit analysis recommendations.

        Args:
            recommendations: List of modification recommendations
            garment: The garment model (for measurements and context)

        Returns:
            List of GeneratedPattern objects
        """
        patterns = []

        for rec in recommendations:
            if rec.modification_type == 'extension':
                pattern = self._generate_extension(rec, garment)
            elif rec.modification_type == 'gusset':
                pattern = self._generate_gusset(rec, garment)
            elif rec.modification_type == 'dart':
                pattern = self._generate_dart_template(rec, garment)
            elif rec.modification_type == 'let_out':
                pattern = self._generate_let_out_panel(rec, garment)
            elif rec.modification_type == 'take_in':
                # Take-in doesn't generate a pattern, just instructions
                continue
            else:
                continue

            if pattern:
                patterns.append(pattern)

        return patterns

    def _generate_extension(self, rec: ModificationRecommendation,
                            garment: GarmentModel) -> Optional[GeneratedPattern]:
        """
        Generate a tapered extension piece.

        NOT a rectangle - tapers to match garment silhouette.
        """
        amount = rec.amount  # Length to add
        zone = rec.issue.body_zone

        # Determine width at top and bottom of extension
        # based on garment measurements
        if zone == BodyZone.ANKLES:
            # Leg extension - taper from current hem to final hem
            # Get ankle/calf measurements from garment
            top_circ = garment.measurements.ankle_circumference or 200
            # Assume slight taper (5% narrower at bottom)
            bottom_circ = top_circ * 0.95

            # For single leg panel (half circumference + seam allowances)
            top_width = top_circ / 2 + self.seam_allowance * 2
            bottom_width = bottom_circ / 2 + self.seam_allowance * 2

            return self._create_tapered_panel(
                name=f"Leg Extension - {rec.issue.body_zone.value}",
                height=amount + self.seam_allowance * 2,
                top_width=top_width,
                bottom_width=bottom_width,
                instructions=rec.instructions
            )

        elif zone == BodyZone.CROTCH:
            # Rise extension
            # Width is waist circumference / 4 (quarter panel)
            waist_circ = garment.measurements.waist_circumference or 800
            width = waist_circ / 4 + self.seam_allowance * 2

            return self._create_rectangular_panel(
                name="Rise Extension",
                width=width,
                height=amount + self.seam_allowance * 2,
                instructions=rec.instructions
            )

        elif zone == BodyZone.WAIST:
            # Torso extension band
            waist_circ = garment.measurements.waist_circumference or 800
            width = waist_circ / 2 + self.seam_allowance * 2

            return self._create_rectangular_panel(
                name="Torso Extension Band",
                width=width,
                height=amount + self.seam_allowance * 2,
                instructions=rec.instructions
            )

        return None

    def _generate_gusset(self, rec: ModificationRecommendation,
                         garment: GarmentModel) -> Optional[GeneratedPattern]:
        """
        Generate a gusset (diamond or football shaped).

        Gussets add ease at stress points without straight seams.
        """
        amount = rec.amount  # Width to add
        zone = rec.issue.body_zone

        if zone == BodyZone.SHOULDERS:
            # Diamond gusset for shoulder
            return self._create_diamond_gusset(
                name="Shoulder Gusset",
                width=amount + self.seam_allowance * 2,
                height=amount * 1.5,  # Slightly taller than wide
                instructions=rec.instructions
            )

        elif zone == BodyZone.CROTCH:
            # Football-shaped crotch gusset
            return self._create_football_gusset(
                name="Crotch Gusset",
                length=amount * 2,  # Long axis
                width=amount,  # Short axis
                instructions=rec.instructions
            )

        elif zone in [BodyZone.THIGHS, BodyZone.KNEES]:
            # Side gusset for leg movement
            return self._create_diamond_gusset(
                name=f"{zone.value.title()} Ease Gusset",
                width=amount + self.seam_allowance * 2,
                height=amount,
                instructions=rec.instructions
            )

        return None

    def _generate_dart_template(self, rec: ModificationRecommendation,
                                 garment: GarmentModel) -> Optional[GeneratedPattern]:
        """
        Generate a dart marking template.

        This is a guide for where to sew darts, not a piece to cut.
        """
        amount = rec.amount  # Amount to take in
        zone = rec.issue.body_zone

        # Dart dimensions based on amount
        dart_width = amount / 2  # Width at widest point
        dart_length = min(amount * 4, 150)  # Don't make darts too long

        return self._create_dart_marker(
            name=f"{zone.value.title()} Dart Guide",
            dart_width=dart_width,
            dart_length=dart_length,
            instructions=rec.instructions
        )

    def _generate_let_out_panel(self, rec: ModificationRecommendation,
                                 garment: GarmentModel) -> Optional[GeneratedPattern]:
        """
        Generate a side panel insert for letting out.

        When there's not enough seam allowance to let out, add a panel.
        """
        amount = rec.amount  # Width to add
        zone = rec.issue.body_zone

        # Panel height depends on zone
        if zone in [BodyZone.HIPS, BodyZone.THIGHS]:
            # From hip to knee
            height = garment.measurements.outseam_length / 2 if garment.measurements.outseam_length else 400
        else:
            height = 200  # Default

        return self._create_tapered_panel(
            name=f"Side Panel Insert - {zone.value}",
            height=height + self.seam_allowance * 2,
            top_width=amount + self.seam_allowance * 2,
            bottom_width=amount * 0.8 + self.seam_allowance * 2,  # Slight taper
            instructions=rec.instructions
        )

    def _create_tapered_panel(self, name: str, height: float,
                               top_width: float, bottom_width: float,
                               instructions: str) -> GeneratedPattern:
        """Create a tapered (trapezoidal) panel"""
        # Define corners (clockwise from top-left)
        top_left = np.array([0, height])
        top_right = np.array([top_width, height])
        bottom_right = np.array([(top_width + bottom_width) / 2 + (top_width - bottom_width) / 2,
                                  0])
        bottom_left = np.array([(top_width - bottom_width) / 2, 0])

        # Adjust for taper centering
        offset = (top_width - bottom_width) / 2
        bottom_left = np.array([offset, 0])
        bottom_right = np.array([offset + bottom_width, 0])

        outline = np.array([top_left, top_right, bottom_right, bottom_left, top_left])

        # Stitch line is inside seam allowance
        stitch_line = self._offset_polygon(outline[:-1], -self.seam_allowance)

        # Add notches at midpoints
        notches = [
            Notch(
                position=np.array([top_width / 2, height]),
                direction=np.array([0, -1]),
                label="TOP"
            ),
            Notch(
                position=np.array([(bottom_left[0] + bottom_right[0]) / 2, 0]),
                direction=np.array([0, 1]),
                label="BOTTOM"
            )
        ]

        # Grain line (vertical, centered)
        grain_line = GrainLine(
            start=np.array([top_width / 2, height * 0.2]),
            end=np.array([top_width / 2, height * 0.8])
        )

        return GeneratedPattern(
            name=name,
            piece_type=PatternPieceType.EXTENSION,
            outline=outline,
            cut_line=outline,
            stitch_line=stitch_line,
            seam_allowance=self.seam_allowance,
            notches=notches,
            grain_line=grain_line,
            labels={
                'center': (np.array([top_width / 2, height / 2]),
                          f"Cut 2\nSA: {self.seam_allowance}mm")
            },
            instructions=instructions,
            area_mm2=self._polygon_area(outline[:-1]),
            dimensions_mm=(max(top_width, bottom_width), height)
        )

    def _create_rectangular_panel(self, name: str, width: float, height: float,
                                    instructions: str) -> GeneratedPattern:
        """Create a simple rectangular panel"""
        outline = np.array([
            [0, height],
            [width, height],
            [width, 0],
            [0, 0],
            [0, height]
        ])

        stitch_line = self._offset_polygon(outline[:-1], -self.seam_allowance)

        notches = [
            Notch(
                position=np.array([width / 2, height]),
                direction=np.array([0, -1]),
                label="TOP"
            ),
            Notch(
                position=np.array([width / 2, 0]),
                direction=np.array([0, 1]),
                label="BOTTOM"
            )
        ]

        grain_line = GrainLine(
            start=np.array([width / 2, height * 0.2]),
            end=np.array([width / 2, height * 0.8])
        )

        return GeneratedPattern(
            name=name,
            piece_type=PatternPieceType.EXTENSION,
            outline=outline,
            cut_line=outline,
            stitch_line=stitch_line,
            seam_allowance=self.seam_allowance,
            notches=notches,
            grain_line=grain_line,
            labels={
                'center': (np.array([width / 2, height / 2]),
                          f"Cut 2\nSA: {self.seam_allowance}mm")
            },
            instructions=instructions,
            area_mm2=width * height,
            dimensions_mm=(width, height)
        )

    def _create_diamond_gusset(self, name: str, width: float, height: float,
                                instructions: str) -> GeneratedPattern:
        """Create a diamond-shaped gusset"""
        # Diamond points
        top = np.array([width / 2, height])
        right = np.array([width, height / 2])
        bottom = np.array([width / 2, 0])
        left = np.array([0, height / 2])

        outline = np.array([top, right, bottom, left, top])
        stitch_line = self._offset_polygon(outline[:-1], -self.seam_allowance)

        notches = [
            Notch(position=top, direction=np.array([0, -1]), label="1"),
            Notch(position=right, direction=np.array([-1, 0]), label="2"),
            Notch(position=bottom, direction=np.array([0, 1]), label="3"),
            Notch(position=left, direction=np.array([1, 0]), label="4")
        ]

        return GeneratedPattern(
            name=name,
            piece_type=PatternPieceType.GUSSET,
            outline=outline,
            cut_line=outline,
            stitch_line=stitch_line,
            seam_allowance=self.seam_allowance,
            notches=notches,
            grain_line=None,  # Gussets often on bias
            labels={
                'center': (np.array([width / 2, height / 2]),
                          f"Cut 1\n(or 2 for pair)\nSA: {self.seam_allowance}mm")
            },
            instructions=instructions,
            area_mm2=(width * height) / 2,
            dimensions_mm=(width, height)
        )

    def _create_football_gusset(self, name: str, length: float, width: float,
                                 instructions: str) -> GeneratedPattern:
        """Create a football/eye-shaped gusset for crotch"""
        # Generate curved football shape
        num_points = 20
        outline_points = []

        # Top curve
        for i in range(num_points):
            t = i / (num_points - 1)
            x = t * length
            # Parabolic curve
            y = width / 2 + (width / 2) * (1 - (2 * t - 1) ** 2)
            outline_points.append([x, y])

        # Bottom curve (reverse)
        for i in range(num_points - 1, -1, -1):
            t = i / (num_points - 1)
            x = t * length
            y = width / 2 - (width / 2) * (1 - (2 * t - 1) ** 2)
            outline_points.append([x, y])

        outline = np.array(outline_points + [outline_points[0]])
        stitch_line = self._offset_polygon(np.array(outline_points), -self.seam_allowance)

        notches = [
            Notch(position=np.array([0, width / 2]), direction=np.array([1, 0]), label="FRONT"),
            Notch(position=np.array([length, width / 2]), direction=np.array([-1, 0]), label="BACK")
        ]

        return GeneratedPattern(
            name=name,
            piece_type=PatternPieceType.GUSSET,
            outline=outline,
            cut_line=outline,
            stitch_line=stitch_line,
            seam_allowance=self.seam_allowance,
            notches=notches,
            grain_line=GrainLine(
                start=np.array([length * 0.3, width / 2]),
                end=np.array([length * 0.7, width / 2])
            ),
            labels={
                'center': (np.array([length / 2, width / 2]),
                          f"Cut 1\nStretch fabric recommended\nSA: {self.seam_allowance}mm")
            },
            instructions=instructions,
            area_mm2=np.pi * (length / 2) * (width / 2) * 0.8,  # Approximate
            dimensions_mm=(length, width)
        )

    def _create_dart_marker(self, name: str, dart_width: float, dart_length: float,
                             instructions: str) -> GeneratedPattern:
        """Create a dart marking template"""
        # Triangle dart shape
        apex = np.array([dart_width / 2, dart_length])
        left = np.array([0, 0])
        right = np.array([dart_width, 0])

        outline = np.array([apex, right, left, apex])

        return GeneratedPattern(
            name=name,
            piece_type=PatternPieceType.DART,
            outline=outline,
            cut_line=outline,  # Darts aren't cut, just folded
            stitch_line=outline,
            seam_allowance=0,  # No seam allowance for dart marker
            notches=[
                Notch(position=apex, direction=np.array([0, -1]), label="APEX"),
                Notch(position=left, direction=np.array([1, 0]), label="FOLD"),
                Notch(position=right, direction=np.array([-1, 0]), label="FOLD")
            ],
            grain_line=None,
            labels={
                'center': (np.array([dart_width / 2, dart_length / 3]),
                          "DART TEMPLATE\nTrace onto garment")
            },
            instructions=instructions,
            area_mm2=(dart_width * dart_length) / 2,
            dimensions_mm=(dart_width, dart_length)
        )

    def _offset_polygon(self, points: np.ndarray, distance: float) -> np.ndarray:
        """
        Offset a polygon inward (negative distance) or outward (positive).

        Simple implementation - may have issues with complex shapes.
        """
        n = len(points)
        offset_points = []

        for i in range(n):
            # Get adjacent points
            prev_pt = points[(i - 1) % n]
            curr_pt = points[i]
            next_pt = points[(i + 1) % n]

            # Edge vectors
            edge1 = curr_pt - prev_pt
            edge2 = next_pt - curr_pt

            # Normals (perpendicular, pointing inward for CCW polygon)
            n1 = np.array([-edge1[1], edge1[0]])
            n2 = np.array([-edge2[1], edge2[0]])

            # Normalize
            n1 = n1 / (np.linalg.norm(n1) + 1e-6)
            n2 = n2 / (np.linalg.norm(n2) + 1e-6)

            # Bisector
            bisector = n1 + n2
            bisector = bisector / (np.linalg.norm(bisector) + 1e-6)

            # Offset point
            offset_points.append(curr_pt + bisector * distance)

        return np.array(offset_points)

    def _polygon_area(self, points: np.ndarray) -> float:
        """Compute area of a 2D polygon"""
        n = len(points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i, 0] * points[j, 1]
            area -= points[j, 0] * points[i, 1]
        return abs(area) / 2.0

    def export_svg(self, pattern: GeneratedPattern,
                   scale: float = 1.0) -> str:
        """
        Export a pattern piece to SVG format.

        Args:
            pattern: The pattern to export
            scale: Scale factor (1.0 = actual size in mm)

        Returns:
            SVG content as string
        """
        if not SVGWRITE_AVAILABLE:
            return self._export_svg_basic(pattern, scale)

        # Calculate dimensions
        width = pattern.dimensions_mm[0] * scale + 40  # Margins
        height = pattern.dimensions_mm[1] * scale + 60

        dwg = svgwrite.Drawing(size=(f"{width}mm", f"{height}mm"),
                               viewBox=f"0 0 {width} {height}")

        # Add styles
        dwg.defs.add(dwg.style("""
            .cut-line { stroke: black; stroke-width: 0.5; fill: none; }
            .stitch-line { stroke: gray; stroke-width: 0.3; fill: none; stroke-dasharray: 3,2; }
            .grain-line { stroke: black; stroke-width: 0.3; fill: none; }
            .notch { stroke: black; stroke-width: 0.3; fill: black; }
            .label { font-family: Arial, sans-serif; font-size: 10px; fill: black; }
            .title { font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; fill: black; }
        """))

        # Transform to SVG coordinates (Y flipped, with margin)
        def transform(pt):
            return (pt[0] * scale + 20,
                    height - 40 - pt[1] * scale)

        # Draw cut line
        points = [transform(p) for p in pattern.cut_line]
        dwg.add(dwg.polyline(points, class_='cut-line'))

        # Draw stitch line
        if len(pattern.stitch_line) > 0:
            stitch_points = [transform(p) for p in pattern.stitch_line]
            stitch_points.append(stitch_points[0])  # Close
            dwg.add(dwg.polyline(stitch_points, class_='stitch-line'))

        # Draw grain line
        if pattern.grain_line:
            start = transform(pattern.grain_line.start)
            end = transform(pattern.grain_line.end)
            dwg.add(dwg.line(start, end, class_='grain-line'))
            # Arrow at end
            arrow_size = 5
            direction = np.array(end) - np.array(start)
            direction = direction / (np.linalg.norm(direction) + 1e-6)
            perp = np.array([-direction[1], direction[0]])
            arrow_pt1 = np.array(end) - direction * arrow_size + perp * arrow_size / 2
            arrow_pt2 = np.array(end) - direction * arrow_size - perp * arrow_size / 2
            dwg.add(dwg.polyline([tuple(arrow_pt1), end, tuple(arrow_pt2)], class_='grain-line'))

        # Draw notches
        for notch in pattern.notches:
            pos = transform(notch.position)
            # Simple notch mark
            notch_length = 5
            end = (pos[0] + notch.direction[0] * notch_length,
                   pos[1] - notch.direction[1] * notch_length)
            dwg.add(dwg.line(pos, end, class_='notch'))
            dwg.add(dwg.text(notch.label, insert=(pos[0] + 3, pos[1] + 3),
                            class_='label'))

        # Add labels
        for label_pos, label_text in pattern.labels.values():
            pos = transform(label_pos)
            lines = label_text.split('\n')
            for i, line in enumerate(lines):
                dwg.add(dwg.text(line, insert=(pos[0], pos[1] + i * 12),
                                class_='label', text_anchor='middle'))

        # Add title
        dwg.add(dwg.text(pattern.name, insert=(width / 2, 15),
                        class_='title', text_anchor='middle'))

        # Add dimensions
        dim_text = f"{pattern.dimensions_mm[0]:.0f}mm × {pattern.dimensions_mm[1]:.0f}mm"
        dwg.add(dwg.text(dim_text, insert=(width / 2, height - 10),
                        class_='label', text_anchor='middle'))

        return dwg.tostring()

    def _export_svg_basic(self, pattern: GeneratedPattern, scale: float = 1.0) -> str:
        """Basic SVG export without svgwrite library"""
        width = pattern.dimensions_mm[0] * scale + 40
        height = pattern.dimensions_mm[1] * scale + 60

        def transform(pt):
            return (pt[0] * scale + 20, height - 40 - pt[1] * scale)

        # Build path
        points = [transform(p) for p in pattern.cut_line]
        path_d = f"M {points[0][0]:.2f},{points[0][1]:.2f} "
        for p in points[1:]:
            path_d += f"L {p[0]:.2f},{p[1]:.2f} "
        path_d += "Z"

        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{width}mm" height="{height}mm"
     viewBox="0 0 {width} {height}">
  <style>
    .cut-line {{ stroke: black; stroke-width: 0.5; fill: none; }}
    .title {{ font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; }}
    .label {{ font-family: Arial, sans-serif; font-size: 10px; }}
  </style>

  <text x="{width/2}" y="15" class="title" text-anchor="middle">{pattern.name}</text>

  <path d="{path_d}" class="cut-line"/>

  <text x="{width/2}" y="{height-10}" class="label" text-anchor="middle">
    {pattern.dimensions_mm[0]:.0f}mm × {pattern.dimensions_mm[1]:.0f}mm | SA: {pattern.seam_allowance}mm
  </text>
</svg>'''
        return svg


def generate_patterns(recommendations: List[Dict],
                      garment_data: Dict,
                      fabric_type: str = 'default') -> Dict[str, Any]:
    """
    Convenience function for API use.

    Args:
        recommendations: List of recommendation dicts from fit analysis
        garment_data: Garment model data
        fabric_type: Fabric type for seam allowance

    Returns:
        Dict with generated patterns and SVG content
    """
    # Reconstruct recommendation objects (simplified)
    from fit_analysis import ModificationRecommendation, FitIssue, FitIssueType, FitIssueSeverity

    recs = []
    for rec_dict in recommendations:
        # Create minimal FitIssue
        issue = FitIssue(
            issue_type=FitIssueType(rec_dict.get('for_issue', 'compression')),
            severity=FitIssueSeverity.MODERATE,
            body_zone=BodyZone(rec_dict.get('zone', 'hips')),
            location=np.array([0, 0, 0]),
            amount=rec_dict.get('amount_mm', 50),
            description=""
        )

        recs.append(ModificationRecommendation(
            issue=issue,
            modification_type=rec_dict.get('type', 'extension'),
            amount=rec_dict.get('amount_mm', 50),
            location=rec_dict.get('location', ''),
            priority=rec_dict.get('priority', 1),
            instructions=rec_dict.get('instructions', '')
        ))

    # Create minimal garment model
    garment = GarmentModel(np.zeros((4, 3)), np.array([[0, 1, 2]]))
    garment.measurements.waist_circumference = garment_data.get('waist_circumference', 800)
    garment.measurements.hip_circumference = garment_data.get('hip_circumference', 1000)
    garment.measurements.ankle_circumference = garment_data.get('ankle_circumference', 250)
    garment.measurements.outseam_length = garment_data.get('outseam_length', 1000)

    # Generate patterns
    generator = PatternGenerator(fabric_type)
    patterns = generator.generate_from_recommendations(recs, garment)

    # Export to SVG
    result = {
        'patterns': [p.to_dict() for p in patterns],
        'svg_content': {}
    }

    for pattern in patterns:
        svg = generator.export_svg(pattern)
        result['svg_content'][pattern.name] = svg

    return result
