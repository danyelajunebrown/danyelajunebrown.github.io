"""
Fit Analysis Module - Make It Cunt v3.0

THE CORE: Compares body mesh to garment mesh to find fit problems.
Identifies compression zones (too tight), gap zones (too loose),
length deficits, and movement conflicts.

Dependencies: numpy, scipy, trimesh (optional)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from scipy.spatial import cKDTree

from body_model import BodyModel, BodyLandmark, MovementEnvelope
from garment_model import GarmentModel, GarmentType


class FitIssueType(Enum):
    """Types of fit problems we can detect"""
    COMPRESSION = "compression"  # Garment too tight (stress, ripping)
    GAP = "gap"  # Garment too loose (tenting, excess fabric)
    TOO_SHORT = "too_short"  # Garment doesn't reach far enough
    MOVEMENT_CONFLICT = "movement_conflict"  # Body movement exceeds garment
    SEAM_STRESS = "seam_stress"  # High stress at a seam line


class FitIssueSeverity(Enum):
    """Severity levels for fit issues"""
    MINOR = "minor"  # Cosmetic, could be ignored
    MODERATE = "moderate"  # Noticeable, should fix
    SEVERE = "severe"  # Functional problem, must fix
    CRITICAL = "critical"  # Will cause damage or extreme discomfort


class BodyZone(Enum):
    """Body zones for localized fit analysis"""
    SHOULDERS = "shoulders"
    BUST = "bust"
    WAIST = "waist"
    HIPS = "hips"
    CROTCH = "crotch"
    THIGHS = "thighs"
    KNEES = "knees"
    CALVES = "calves"
    ANKLES = "ankles"
    TORSO_FRONT = "torso_front"
    TORSO_BACK = "torso_back"


@dataclass
class FitIssue:
    """A specific fit problem detected"""
    issue_type: FitIssueType
    severity: FitIssueSeverity
    body_zone: BodyZone
    location: np.ndarray  # 3D location of the issue
    amount: float  # How much (in mm) - negative for compression, positive for gap
    description: str
    affected_vertices: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.issue_type.value,
            'severity': self.severity.value,
            'zone': self.body_zone.value,
            'location': self.location.tolist(),
            'amount_mm': float(self.amount),
            'description': self.description,
            'affected_vertex_count': len(self.affected_vertices)
        }


@dataclass
class ModificationRecommendation:
    """A recommended modification to fix a fit issue"""
    issue: FitIssue
    modification_type: str  # 'extension', 'gusset', 'dart', 'let_out', 'take_in'
    amount: float  # How much to modify (mm)
    location: str  # Where to apply
    priority: int  # 1 = highest priority
    instructions: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.modification_type,
            'for_issue': self.issue.issue_type.value,
            'zone': self.issue.body_zone.value,
            'amount_mm': float(self.amount),
            'location': self.location,
            'priority': self.priority,
            'instructions': self.instructions
        }


@dataclass
class FitAnalysisResult:
    """Complete fit analysis results"""
    issues: List[FitIssue]
    recommendations: List[ModificationRecommendation]
    overall_fit_score: float  # 0-100, higher is better
    distance_map: Optional[np.ndarray] = None  # Per-vertex distance body→garment

    def to_dict(self) -> Dict[str, Any]:
        return {
            'issues': [i.to_dict() for i in self.issues],
            'recommendations': [r.to_dict() for r in self.recommendations],
            'overall_fit_score': float(self.overall_fit_score),
            'issue_count': len(self.issues),
            'issues_by_type': self._count_by_type(),
            'issues_by_zone': self._count_by_zone()
        }

    def _count_by_type(self) -> Dict[str, int]:
        counts = {}
        for issue in self.issues:
            t = issue.issue_type.value
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _count_by_zone(self) -> Dict[str, int]:
        counts = {}
        for issue in self.issues:
            z = issue.body_zone.value
            counts[z] = counts.get(z, 0) + 1
        return counts


class FitAnalyzer:
    """
    Analyzes fit between a body and garment mesh.

    The key operation: for each point on the body, find the distance
    to the nearest point on the garment. This creates a "distance map"
    that shows where the garment is too tight (negative) or too loose
    (positive).
    """

    # Thresholds for fit issues (in mm)
    COMPRESSION_THRESHOLD = -5  # Negative = body outside garment
    GAP_THRESHOLD_MINOR = 20
    GAP_THRESHOLD_MODERATE = 40
    GAP_THRESHOLD_SEVERE = 60
    SEAM_STRESS_THRESHOLD = -10

    def __init__(self, body: BodyModel, garment: GarmentModel,
                 movement_envelope: Optional[MovementEnvelope] = None):
        """
        Initialize fit analyzer.

        Args:
            body: Analyzed body model
            garment: Analyzed garment model
            movement_envelope: Optional movement envelope for dynamic fit
        """
        self.body = body
        self.garment = garment
        self.movement_envelope = movement_envelope

        # Build spatial index for garment
        self._garment_tree = cKDTree(garment.vertices)

    def analyze(self) -> FitAnalysisResult:
        """
        Perform complete fit analysis.

        1. Compute body→garment distance map
        2. Identify compression zones
        3. Identify gap zones
        4. Check for length deficits
        5. Check movement envelope conflicts
        6. Generate recommendations
        """
        issues = []

        # Compute distance map
        distance_map = self._compute_distance_map()

        # Find compression zones (body too big for garment)
        compression_issues = self._find_compression_zones(distance_map)
        issues.extend(compression_issues)

        # Find gap zones (garment too loose)
        gap_issues = self._find_gap_zones(distance_map)
        issues.extend(gap_issues)

        # Check length
        length_issues = self._check_length()
        issues.extend(length_issues)

        # Check movement envelope
        if self.movement_envelope:
            movement_issues = self._check_movement_conflicts()
            issues.extend(movement_issues)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues)

        # Compute overall fit score
        fit_score = self._compute_fit_score(issues)

        return FitAnalysisResult(
            issues=issues,
            recommendations=recommendations,
            overall_fit_score=fit_score,
            distance_map=distance_map
        )

    def _compute_distance_map(self) -> np.ndarray:
        """
        Compute signed distance from each body vertex to garment surface.

        Positive = body inside garment (good, or gap if too large)
        Negative = body outside garment (compression)

        Uses ray casting to determine inside/outside.
        """
        # Find nearest garment point for each body vertex
        distances, indices = self._garment_tree.query(self.body.vertices)

        # Determine sign using surface normals
        # If body point is in direction of garment normal = inside (positive)
        # If body point is opposite garment normal = outside (negative)

        signed_distances = np.zeros(len(self.body.vertices))

        for i, (dist, garment_idx) in enumerate(zip(distances, indices)):
            body_point = self.body.vertices[i]
            garment_point = self.garment.vertices[garment_idx]

            # Vector from garment to body
            direction = body_point - garment_point

            # Get approximate surface normal at garment point
            # (simplified: use average of adjacent face normals)
            normal = self._get_vertex_normal(garment_idx)

            # Dot product determines inside/outside
            dot = np.dot(direction, normal)

            # Positive dot = body is in normal direction = outside garment = compression
            # Negative dot = body is opposite normal direction = inside garment = ok/gap
            signed_distances[i] = -np.sign(dot) * dist

        return signed_distances

    def _get_vertex_normal(self, vertex_idx: int) -> np.ndarray:
        """Get the normal vector at a garment vertex"""
        # Find faces containing this vertex
        adjacent_faces = []
        for face_idx, face in enumerate(self.garment.faces):
            if vertex_idx in face:
                adjacent_faces.append(face_idx)

        if not adjacent_faces:
            return np.array([0, 1, 0])  # Default up

        # Average the normals
        normals = []
        for face_idx in adjacent_faces:
            face = self.garment.faces[face_idx]
            v0, v1, v2 = self.garment.vertices[face]
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            length = np.linalg.norm(normal)
            if length > 0:
                normals.append(normal / length)

        if not normals:
            return np.array([0, 1, 0])

        avg_normal = np.mean(normals, axis=0)
        length = np.linalg.norm(avg_normal)
        if length > 0:
            return avg_normal / length
        return np.array([0, 1, 0])

    def _classify_body_zone(self, vertex: np.ndarray) -> BodyZone:
        """Classify which body zone a vertex belongs to"""
        height = vertex[1]
        rel_height = (height - self.body.min_y) / self.body.height

        # Use landmarks if available
        landmarks = self.body.landmarks

        # Check shoulder zone
        if BodyLandmark.SHOULDER_CENTER in landmarks:
            shoulder_h = landmarks[BodyLandmark.SHOULDER_CENTER][1]
            if abs(height - shoulder_h) < 100:
                return BodyZone.SHOULDERS

        # Check bust zone
        if BodyLandmark.BUST_APEX_LEFT in landmarks:
            bust_h = landmarks[BodyLandmark.BUST_APEX_LEFT][1]
            if abs(height - bust_h) < 100:
                return BodyZone.BUST

        # Check waist zone
        if BodyLandmark.WAIST in landmarks:
            waist_h = landmarks[BodyLandmark.WAIST][1]
            if abs(height - waist_h) < 100:
                return BodyZone.WAIST

        # Check hip zone
        if BodyLandmark.HIP in landmarks:
            hip_h = landmarks[BodyLandmark.HIP][1]
            if abs(height - hip_h) < 100:
                return BodyZone.HIPS

        # Check crotch zone
        if BodyLandmark.CROTCH in landmarks:
            crotch_h = landmarks[BodyLandmark.CROTCH][1]
            if abs(height - crotch_h) < 80:
                return BodyZone.CROTCH

        # Check knee zone
        if BodyLandmark.LEFT_KNEE in landmarks:
            knee_h = landmarks[BodyLandmark.LEFT_KNEE][1]
            if abs(height - knee_h) < 80:
                return BodyZone.KNEES

        # Fallback to relative height
        if rel_height > 0.85:
            return BodyZone.SHOULDERS
        elif rel_height > 0.7:
            return BodyZone.BUST
        elif rel_height > 0.55:
            return BodyZone.WAIST
        elif rel_height > 0.4:
            return BodyZone.HIPS
        elif rel_height > 0.3:
            return BodyZone.THIGHS
        elif rel_height > 0.2:
            return BodyZone.KNEES
        elif rel_height > 0.1:
            return BodyZone.CALVES
        else:
            return BodyZone.ANKLES

    def _find_compression_zones(self, distance_map: np.ndarray) -> List[FitIssue]:
        """Find areas where body is compressed by garment"""
        issues = []

        # Find vertices with significant compression
        compressed = distance_map < self.COMPRESSION_THRESHOLD
        compressed_indices = np.where(compressed)[0]

        if len(compressed_indices) == 0:
            return issues

        # Group by body zone
        zones = {}
        for idx in compressed_indices:
            zone = self._classify_body_zone(self.body.vertices[idx])
            if zone not in zones:
                zones[zone] = {'indices': [], 'distances': []}
            zones[zone]['indices'].append(idx)
            zones[zone]['distances'].append(distance_map[idx])

        # Create issue for each zone
        for zone, data in zones.items():
            indices = data['indices']
            distances = data['distances']

            avg_compression = np.mean(distances)
            max_compression = np.min(distances)  # Most negative

            # Determine severity
            if max_compression < -30:
                severity = FitIssueSeverity.CRITICAL
            elif max_compression < -20:
                severity = FitIssueSeverity.SEVERE
            elif max_compression < -10:
                severity = FitIssueSeverity.MODERATE
            else:
                severity = FitIssueSeverity.MINOR

            # Center of compression zone
            center = self.body.vertices[indices].mean(axis=0)

            # Zone-specific descriptions
            descriptions = {
                BodyZone.SHOULDERS: "Shoulder compression - risk of ripping at shoulder seams",
                BodyZone.BUST: "Bust compression - garment pulling across chest",
                BodyZone.WAIST: "Waist compression - garment too tight at waist",
                BodyZone.HIPS: "Hip compression - garment restricting hip movement",
                BodyZone.CROTCH: "Crotch compression - insufficient rise",
                BodyZone.THIGHS: "Thigh compression - legs too tight",
                BodyZone.KNEES: "Knee compression - restricted knee bend",
                BodyZone.CALVES: "Calf compression - lower leg too tight",
                BodyZone.ANKLES: "Ankle compression - hem too tight",
            }

            issues.append(FitIssue(
                issue_type=FitIssueType.COMPRESSION,
                severity=severity,
                body_zone=zone,
                location=center,
                amount=avg_compression,
                description=descriptions.get(zone, f"Compression in {zone.value}"),
                affected_vertices=indices
            ))

        return issues

    def _find_gap_zones(self, distance_map: np.ndarray) -> List[FitIssue]:
        """Find areas where garment is too loose (tenting)"""
        issues = []

        # Find vertices with significant gaps
        gaps = distance_map > self.GAP_THRESHOLD_MINOR
        gap_indices = np.where(gaps)[0]

        if len(gap_indices) == 0:
            return issues

        # Group by body zone
        zones = {}
        for idx in gap_indices:
            zone = self._classify_body_zone(self.body.vertices[idx])
            if zone not in zones:
                zones[zone] = {'indices': [], 'distances': []}
            zones[zone]['indices'].append(idx)
            zones[zone]['distances'].append(distance_map[idx])

        # Create issue for each zone
        for zone, data in zones.items():
            indices = data['indices']
            distances = data['distances']

            avg_gap = np.mean(distances)
            max_gap = np.max(distances)

            # Determine severity
            if max_gap > self.GAP_THRESHOLD_SEVERE:
                severity = FitIssueSeverity.SEVERE
            elif max_gap > self.GAP_THRESHOLD_MODERATE:
                severity = FitIssueSeverity.MODERATE
            else:
                severity = FitIssueSeverity.MINOR

            # Center of gap zone
            center = self.body.vertices[indices].mean(axis=0)

            # Zone-specific descriptions for "lack of curves" issue
            descriptions = {
                BodyZone.BUST: "Bust gap - tenting due to less projection than garment expects",
                BodyZone.HIPS: "Hip gap - excess fabric due to less hip curve",
                BodyZone.WAIST: "Waist gap - garment loose at waist",
                BodyZone.THIGHS: "Thigh gap - excess fabric in thigh area",
            }

            issues.append(FitIssue(
                issue_type=FitIssueType.GAP,
                severity=severity,
                body_zone=zone,
                location=center,
                amount=avg_gap,
                description=descriptions.get(zone, f"Excess fabric in {zone.value}"),
                affected_vertices=indices
            ))

        return issues

    def _check_length(self) -> List[FitIssue]:
        """Check if garment is long enough for body"""
        issues = []

        body_measurements = self.body.measurements
        garment_measurements = self.garment.measurements

        # Check inseam
        if body_measurements.inseam > 0 and garment_measurements.inseam_length > 0:
            deficit = body_measurements.inseam - garment_measurements.inseam_length
            if deficit > 10:  # More than 10mm short
                severity = FitIssueSeverity.SEVERE if deficit > 50 else \
                          FitIssueSeverity.MODERATE if deficit > 25 else \
                          FitIssueSeverity.MINOR

                issues.append(FitIssue(
                    issue_type=FitIssueType.TOO_SHORT,
                    severity=severity,
                    body_zone=BodyZone.ANKLES,
                    location=np.array([0, self.body.min_y, 0]),
                    amount=deficit,
                    description=f"Inseam {deficit:.0f}mm too short for body"
                ))

        # Check outseam
        if body_measurements.outseam > 0 and garment_measurements.outseam_length > 0:
            deficit = body_measurements.outseam - garment_measurements.outseam_length
            if deficit > 10:
                severity = FitIssueSeverity.SEVERE if deficit > 50 else \
                          FitIssueSeverity.MODERATE if deficit > 25 else \
                          FitIssueSeverity.MINOR

                issues.append(FitIssue(
                    issue_type=FitIssueType.TOO_SHORT,
                    severity=severity,
                    body_zone=BodyZone.ANKLES,
                    location=np.array([0, self.body.min_y, 0]),
                    amount=deficit,
                    description=f"Outseam {deficit:.0f}mm too short"
                ))

        # Check rise
        if body_measurements.front_rise > 0 and garment_measurements.front_rise > 0:
            deficit = body_measurements.front_rise - garment_measurements.front_rise
            if deficit > 10:
                severity = FitIssueSeverity.SEVERE if deficit > 30 else \
                          FitIssueSeverity.MODERATE

                issues.append(FitIssue(
                    issue_type=FitIssueType.TOO_SHORT,
                    severity=severity,
                    body_zone=BodyZone.CROTCH,
                    location=self.body.landmarks.get(BodyLandmark.CROTCH,
                                                      np.array([0, self.body.height * 0.4, 0])),
                    amount=deficit,
                    description=f"Rise {deficit:.0f}mm too short - will pull at crotch"
                ))

        # Check torso length
        if body_measurements.torso_length > 0 and garment_measurements.body_length > 0:
            # For shirts, body_length is torso
            if self.garment.garment_type == GarmentType.SHIRT:
                deficit = body_measurements.torso_length - garment_measurements.body_length
                if deficit > 20:
                    issues.append(FitIssue(
                        issue_type=FitIssueType.TOO_SHORT,
                        severity=FitIssueSeverity.MODERATE,
                        body_zone=BodyZone.WAIST,
                        location=self.body.landmarks.get(BodyLandmark.WAIST,
                                                          np.array([0, self.body.height * 0.55, 0])),
                        amount=deficit,
                        description=f"Torso {deficit:.0f}mm too short - will ride up"
                    ))

        return issues

    def _check_movement_conflicts(self) -> List[FitIssue]:
        """Check if movement envelope conflicts with garment"""
        if not self.movement_envelope:
            return []

        issues = []

        # Use expanded vertices for distance check
        expanded_verts = self.movement_envelope.expanded_vertices

        # Find nearest garment points
        distances, _ = self._garment_tree.query(expanded_verts)

        # Where the movement envelope extends beyond the garment
        conflicts = distances > 0  # Movement needs space garment doesn't provide

        # Group by zone
        for i, (dist, is_conflict) in enumerate(zip(distances, conflicts)):
            if not is_conflict or dist < 20:  # Need significant space
                continue

            zone = self._classify_body_zone(self.body.vertices[i])

            # Only report significant movement conflicts
            if dist > 30:
                issues.append(FitIssue(
                    issue_type=FitIssueType.MOVEMENT_CONFLICT,
                    severity=FitIssueSeverity.MODERATE,
                    body_zone=zone,
                    location=expanded_verts[i],
                    amount=dist,
                    description=f"Movement restricted in {zone.value} - need {dist:.0f}mm more ease"
                ))

        # Deduplicate by zone (keep worst case)
        zone_issues = {}
        for issue in issues:
            if issue.body_zone not in zone_issues:
                zone_issues[issue.body_zone] = issue
            elif issue.amount > zone_issues[issue.body_zone].amount:
                zone_issues[issue.body_zone] = issue

        return list(zone_issues.values())

    def _generate_recommendations(self, issues: List[FitIssue]) -> List[ModificationRecommendation]:
        """Generate specific modification recommendations for each issue"""
        recommendations = []
        priority = 1

        # Sort issues by severity
        sorted_issues = sorted(issues,
                               key=lambda i: (i.severity.value, i.amount),
                               reverse=True)

        for issue in sorted_issues:
            rec = self._recommend_for_issue(issue, priority)
            if rec:
                recommendations.append(rec)
                priority += 1

        return recommendations

    def _recommend_for_issue(self, issue: FitIssue,
                              priority: int) -> Optional[ModificationRecommendation]:
        """Generate a specific recommendation for an issue"""

        if issue.issue_type == FitIssueType.COMPRESSION:
            # Need to let out or add gusset
            if issue.body_zone == BodyZone.SHOULDERS:
                return ModificationRecommendation(
                    issue=issue,
                    modification_type='gusset',
                    amount=abs(issue.amount) + 20,  # Extra for ease
                    location='shoulder_seam',
                    priority=priority,
                    instructions=f"Add diamond gusset at shoulder seam. "
                                f"Gusset should add {abs(issue.amount) + 20:.0f}mm width. "
                                f"Reinforce seam to prevent future ripping."
                )
            elif issue.body_zone in [BodyZone.HIPS, BodyZone.THIGHS]:
                return ModificationRecommendation(
                    issue=issue,
                    modification_type='let_out',
                    amount=abs(issue.amount) + 10,
                    location='side_seam',
                    priority=priority,
                    instructions=f"Let out side seams by {abs(issue.amount) + 10:.0f}mm. "
                                f"If insufficient seam allowance, add side panel insert."
                )
            elif issue.body_zone == BodyZone.CROTCH:
                return ModificationRecommendation(
                    issue=issue,
                    modification_type='gusset',
                    amount=abs(issue.amount) + 30,
                    location='crotch',
                    priority=priority,
                    instructions=f"Add crotch gusset for {abs(issue.amount) + 30:.0f}mm "
                                f"additional room. Use stretch fabric for comfort."
                )

        elif issue.issue_type == FitIssueType.GAP:
            # Need to take in with darts or seams
            if issue.body_zone == BodyZone.BUST:
                return ModificationRecommendation(
                    issue=issue,
                    modification_type='dart',
                    amount=issue.amount,
                    location='bust',
                    priority=priority,
                    instructions=f"Add bust darts to remove {issue.amount:.0f}mm excess. "
                                f"Position darts from side seam toward bust apex. "
                                f"This addresses tenting from less projection."
                )
            elif issue.body_zone == BodyZone.WAIST:
                return ModificationRecommendation(
                    issue=issue,
                    modification_type='take_in',
                    amount=issue.amount,
                    location='waist_seam',
                    priority=priority,
                    instructions=f"Take in waist by {issue.amount:.0f}mm at side seams. "
                                f"Taper gradually into hip for smooth line."
                )
            elif issue.body_zone == BodyZone.HIPS:
                return ModificationRecommendation(
                    issue=issue,
                    modification_type='take_in',
                    amount=issue.amount,
                    location='side_seam',
                    priority=priority,
                    instructions=f"Take in hips by {issue.amount:.0f}mm at side seams."
                )

        elif issue.issue_type == FitIssueType.TOO_SHORT:
            # Need extension
            if issue.body_zone == BodyZone.ANKLES:
                return ModificationRecommendation(
                    issue=issue,
                    modification_type='extension',
                    amount=issue.amount + 25,  # Extra for hem
                    location='hem',
                    priority=priority,
                    instructions=f"Add {issue.amount + 25:.0f}mm extension at hem. "
                                f"Match leg taper - measure circumference at current hem "
                                f"and desired final hem. Includes 25mm hem allowance."
                )
            elif issue.body_zone == BodyZone.CROTCH:
                return ModificationRecommendation(
                    issue=issue,
                    modification_type='extension',
                    amount=issue.amount,
                    location='rise',
                    priority=priority,
                    instructions=f"Add {issue.amount:.0f}mm to rise. "
                                f"Extend waistband upward, maintaining shape. "
                                f"Critical for long-torso fit."
                )
            elif issue.body_zone == BodyZone.WAIST:
                return ModificationRecommendation(
                    issue=issue,
                    modification_type='extension',
                    amount=issue.amount,
                    location='torso_length',
                    priority=priority,
                    instructions=f"Add {issue.amount:.0f}mm to body length. "
                                f"Insert horizontal band below waist or "
                                f"extend hem to prevent ride-up."
                )

        elif issue.issue_type == FitIssueType.MOVEMENT_CONFLICT:
            # Need ease addition
            return ModificationRecommendation(
                issue=issue,
                modification_type='gusset',
                amount=issue.amount,
                location=f'{issue.body_zone.value}_ease',
                priority=priority,
                instructions=f"Add ease gusset at {issue.body_zone.value} for movement. "
                            f"Required additional space: {issue.amount:.0f}mm. "
                            f"Use stretch fabric or action pleats for dynamic movement."
            )

        return None

    def _compute_fit_score(self, issues: List[FitIssue]) -> float:
        """
        Compute overall fit score 0-100.

        100 = Perfect fit
        80-99 = Good fit with minor issues
        60-79 = Acceptable with modifications
        40-59 = Poor fit, significant work needed
        0-39 = Very poor fit
        """
        if not issues:
            return 100.0

        # Deductions based on severity
        deductions = {
            FitIssueSeverity.MINOR: 3,
            FitIssueSeverity.MODERATE: 8,
            FitIssueSeverity.SEVERE: 15,
            FitIssueSeverity.CRITICAL: 25
        }

        total_deduction = sum(deductions[i.severity] for i in issues)

        return max(0.0, 100.0 - total_deduction)


def analyze_fit(body_vertices: np.ndarray, body_faces: np.ndarray,
                garment_vertices: np.ndarray, garment_faces: np.ndarray,
                movement_profile: str = "wild",
                garment_type: str = None) -> Dict[str, Any]:
    """
    Convenience function for API use.

    Args:
        body_vertices: Body mesh vertices
        body_faces: Body mesh faces
        garment_vertices: Garment mesh vertices
        garment_faces: Garment mesh faces
        movement_profile: "default" or "wild"
        garment_type: Optional garment type

    Returns:
        Complete fit analysis results
    """
    # Analyze body
    body = BodyModel(body_vertices, body_faces)
    body.analyze()

    # Generate movement envelope
    envelope = body.generate_movement_envelope(movement_profile)

    # Analyze garment
    garment = GarmentModel(garment_vertices, garment_faces)
    garment.analyze(garment_type)

    # Perform fit analysis
    analyzer = FitAnalyzer(body, garment, envelope)
    result = analyzer.analyze()

    return {
        'fit_analysis': result.to_dict(),
        'body_summary': {
            'measurements': body.measurements.to_dict(),
            'landmark_count': len(body.landmarks)
        },
        'garment_summary': {
            'type': garment.garment_type.value,
            'measurements': garment.measurements.to_dict(),
            'seam_count': len(garment.seams),
            'piece_count': len(garment.pattern_pieces)
        }
    }
