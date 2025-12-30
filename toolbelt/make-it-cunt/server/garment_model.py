"""
Garment Model Module - Make It Cunt v3.0

Analyzes 3D garment scans to detect seams, structure, and extract pattern pieces.
Designed for garments scanned on a dress form.

Dependencies: numpy, scipy, trimesh (optional)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from scipy.spatial import cKDTree
from scipy.signal import find_peaks

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False


class GarmentType(Enum):
    """Types of garments we can analyze"""
    PANTS = "pants"
    SHIRT = "shirt"
    DRESS = "dress"
    SKIRT = "skirt"
    JACKET = "jacket"
    UNKNOWN = "unknown"


class SeamType(Enum):
    """Types of seams in garments"""
    SIDE_SEAM = "side_seam"
    INSEAM = "inseam"
    OUTSEAM = "outseam"
    CENTER_FRONT = "center_front"
    CENTER_BACK = "center_back"
    SHOULDER = "shoulder"
    ARMHOLE = "armhole"
    WAISTBAND = "waistband"
    HEM = "hem"
    CROTCH = "crotch"
    UNKNOWN = "unknown"


@dataclass
class Seam:
    """Represents a seam line on the garment"""
    seam_type: SeamType
    vertices: np.ndarray  # Ordered vertices along the seam
    length: float
    start_point: np.ndarray
    end_point: np.ndarray

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.seam_type.value,
            'length': float(self.length),
            'start': self.start_point.tolist(),
            'end': self.end_point.tolist(),
            'vertex_count': len(self.vertices)
        }


@dataclass
class PatternPiece:
    """A 2D pattern piece extracted from the 3D garment"""
    name: str
    vertices_3d: np.ndarray  # Original 3D vertices
    vertices_2d: np.ndarray  # Flattened 2D vertices
    faces: np.ndarray  # Face indices for this piece
    boundary: np.ndarray  # Ordered boundary vertices (2D)
    area: float  # Area in original units squared
    seams: List[str]  # Which seams border this piece

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'vertex_count': len(self.vertices_3d),
            'face_count': len(self.faces),
            'area': float(self.area),
            'seams': self.seams,
            'bounds_2d': {
                'min': self.vertices_2d.min(axis=0).tolist(),
                'max': self.vertices_2d.max(axis=0).tolist()
            }
        }


@dataclass
class GarmentMeasurements:
    """Measurements extracted from garment mesh"""
    # For pants
    waist_circumference: float = 0.0
    hip_circumference: float = 0.0
    thigh_circumference: float = 0.0
    knee_circumference: float = 0.0
    ankle_circumference: float = 0.0
    inseam_length: float = 0.0
    outseam_length: float = 0.0
    front_rise: float = 0.0
    back_rise: float = 0.0

    # For shirts
    chest_circumference: float = 0.0
    shoulder_width: float = 0.0
    sleeve_length: float = 0.0
    body_length: float = 0.0

    # General
    total_height: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {k: v for k, v in self.__dict__.items() if v > 0}


class GarmentModel:
    """
    Analyzes a 3D garment scan to detect structure and extract pattern pieces.

    Key capabilities:
    1. Detect garment type from shape
    2. Find seam lines (ridges, edges, stitching lines)
    3. Segment into pattern pieces
    4. UV unwrap pieces to 2D patterns
    """

    def __init__(self, vertices: np.ndarray, faces: np.ndarray):
        """
        Initialize with mesh data.

        Args:
            vertices: Nx3 array of vertex positions
            faces: Mx3 array of face indices
        """
        self.vertices = vertices
        self.faces = faces

        # Mesh bounds
        self.min_y = vertices[:, 1].min()
        self.max_y = vertices[:, 1].max()
        self.height = self.max_y - self.min_y

        # Storage
        self.garment_type = GarmentType.UNKNOWN
        self.seams: List[Seam] = []
        self.pattern_pieces: List[PatternPiece] = []
        self.measurements = GarmentMeasurements()

        # Mesh analysis helpers
        self._edge_to_faces: Dict[Tuple[int, int], List[int]] = {}
        self._vertex_to_faces: Dict[int, Set[int]] = {}
        self._build_adjacency()

    def _build_adjacency(self):
        """Build edge and vertex adjacency maps"""
        for face_idx, face in enumerate(self.faces):
            for i in range(3):
                v1, v2 = face[i], face[(i + 1) % 3]
                edge = tuple(sorted([v1, v2]))

                if edge not in self._edge_to_faces:
                    self._edge_to_faces[edge] = []
                self._edge_to_faces[edge].append(face_idx)

                if v1 not in self._vertex_to_faces:
                    self._vertex_to_faces[v1] = set()
                self._vertex_to_faces[v1].add(face_idx)

    def analyze(self, garment_type: str = None) -> 'GarmentModel':
        """
        Full analysis pipeline.

        1. Detect or set garment type
        2. Find seam lines
        3. Extract measurements
        4. Segment into pattern pieces
        """
        if garment_type:
            self.garment_type = GarmentType(garment_type)
        else:
            self._detect_garment_type()

        self._detect_seams()
        self._extract_measurements()
        self._segment_pattern_pieces()

        return self

    def _detect_garment_type(self):
        """
        Detect garment type from mesh shape.

        Heuristics:
        - Pants: Two leg tubes below a unified top
        - Shirt: Single tube with arm holes
        - Dress: Single tube, longer
        """
        # Analyze cross-sections at different heights
        heights = np.linspace(self.min_y, self.max_y, 20)
        slice_thickness = self.height / 20

        # Count number of separate "islands" at each height
        components_per_height = []

        for height in heights:
            mask = np.abs(self.vertices[:, 1] - height) < slice_thickness
            if mask.sum() < 10:
                components_per_height.append(0)
                continue

            points_2d = self.vertices[mask][:, [0, 2]]

            # Simple component counting via clustering
            from scipy.cluster.hierarchy import fclusterdata
            try:
                if len(points_2d) > 1:
                    clusters = fclusterdata(points_2d, t=50, criterion='distance')
                    n_components = len(set(clusters))
                else:
                    n_components = 1
            except:
                n_components = 1

            components_per_height.append(n_components)

        components_per_height = np.array(components_per_height)

        # Pants: 2 components in lower half, 1 in upper half
        lower_half = components_per_height[:len(components_per_height) // 2]
        upper_half = components_per_height[len(components_per_height) // 2:]

        if np.mean(lower_half) > 1.5 and np.mean(upper_half) < 1.5:
            self.garment_type = GarmentType.PANTS
        elif self.height > 1000:  # Long garment
            self.garment_type = GarmentType.DRESS
        else:
            self.garment_type = GarmentType.SHIRT

    def _detect_seams(self):
        """
        Detect seam lines on the garment.

        Seams appear as:
        1. Sharp edges (high dihedral angle between adjacent faces)
        2. Ridges in the surface
        3. Boundary edges (edges with only one adjacent face)
        """
        # Find boundary edges (single-face edges)
        boundary_edges = []
        for edge, faces in self._edge_to_faces.items():
            if len(faces) == 1:
                boundary_edges.append(edge)

        # Find sharp edges (high dihedral angle)
        sharp_edges = []
        for edge, face_indices in self._edge_to_faces.items():
            if len(face_indices) == 2:
                # Compute dihedral angle
                f1, f2 = face_indices
                n1 = self._face_normal(f1)
                n2 = self._face_normal(f2)

                cos_angle = np.clip(np.dot(n1, n2), -1, 1)
                angle = np.arccos(cos_angle)

                # Sharp edge threshold (> 30 degrees)
                if angle > np.radians(30):
                    sharp_edges.append(edge)

        # Chain edges into seam lines
        seam_edges = set(boundary_edges + sharp_edges)
        self.seams = self._chain_edges_to_seams(seam_edges)

    def _face_normal(self, face_idx: int) -> np.ndarray:
        """Compute normal vector for a face"""
        face = self.faces[face_idx]
        v0, v1, v2 = self.vertices[face]

        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)

        length = np.linalg.norm(normal)
        if length > 0:
            normal = normal / length

        return normal

    def _chain_edges_to_seams(self, edges: Set[Tuple[int, int]]) -> List[Seam]:
        """Chain connected edges into seam lines"""
        if not edges:
            return []

        # Build vertex adjacency for seam edges
        vertex_to_edges = {}
        for edge in edges:
            for v in edge:
                if v not in vertex_to_edges:
                    vertex_to_edges[v] = []
                vertex_to_edges[v].append(edge)

        # Find chains
        seams = []
        used_edges = set()

        for start_edge in edges:
            if start_edge in used_edges:
                continue

            # Start a new chain
            chain_vertices = list(start_edge)
            used_edges.add(start_edge)

            # Extend in both directions
            for direction in [0, -1]:  # Forward, backward
                current_vertex = chain_vertices[direction]

                while True:
                    # Find connected edges
                    connected = [e for e in vertex_to_edges.get(current_vertex, [])
                                 if e not in used_edges]

                    if not connected:
                        break

                    # Take the first connected edge
                    next_edge = connected[0]
                    used_edges.add(next_edge)

                    # Add the other vertex
                    next_vertex = next_edge[0] if next_edge[1] == current_vertex else next_edge[1]

                    if direction == 0:
                        chain_vertices.append(next_vertex)
                    else:
                        chain_vertices.insert(0, next_vertex)

                    current_vertex = next_vertex

            if len(chain_vertices) > 3:  # Minimum seam length
                seam_verts = self.vertices[chain_vertices]
                length = np.sum(np.linalg.norm(np.diff(seam_verts, axis=0), axis=1))

                seam_type = self._classify_seam(seam_verts)

                seams.append(Seam(
                    seam_type=seam_type,
                    vertices=seam_verts,
                    length=length,
                    start_point=seam_verts[0],
                    end_point=seam_verts[-1]
                ))

        return seams

    def _classify_seam(self, seam_vertices: np.ndarray) -> SeamType:
        """
        Classify a seam based on its position and orientation.
        """
        # Get seam characteristics
        center = seam_vertices.mean(axis=0)
        direction = seam_vertices[-1] - seam_vertices[0]
        direction = direction / (np.linalg.norm(direction) + 1e-6)

        # Height range
        min_y = seam_vertices[:, 1].min()
        max_y = seam_vertices[:, 1].max()
        height_range = max_y - min_y

        # Relative position
        rel_height = (center[1] - self.min_y) / self.height
        rel_x = center[0]

        # Is it mostly vertical?
        is_vertical = abs(direction[1]) > 0.7

        # Is it mostly horizontal?
        is_horizontal = abs(direction[1]) < 0.3

        # Classification based on garment type
        if self.garment_type == GarmentType.PANTS:
            if is_vertical:
                if rel_height < 0.3:
                    # Lower vertical seam
                    if abs(rel_x) < 50:  # Near center
                        return SeamType.INSEAM
                    else:
                        return SeamType.OUTSEAM
                elif rel_height > 0.7:
                    if rel_x > 0:
                        return SeamType.SIDE_SEAM
                    else:
                        return SeamType.SIDE_SEAM
            elif is_horizontal:
                if rel_height > 0.9:
                    return SeamType.WAISTBAND
                elif rel_height < 0.1:
                    return SeamType.HEM
                else:
                    return SeamType.CROTCH

        elif self.garment_type in [GarmentType.SHIRT, GarmentType.DRESS]:
            if is_vertical:
                if abs(center[2]) < 30:  # Near front/back center
                    if center[2] > 0:
                        return SeamType.CENTER_FRONT
                    else:
                        return SeamType.CENTER_BACK
                else:
                    return SeamType.SIDE_SEAM
            elif is_horizontal:
                if rel_height > 0.85:
                    return SeamType.SHOULDER
                elif rel_height < 0.1:
                    return SeamType.HEM

        return SeamType.UNKNOWN

    def _extract_measurements(self):
        """Extract measurements from the garment mesh"""
        # Generate cross-sections at key heights
        heights = np.linspace(self.min_y, self.max_y, 50)
        slice_thickness = self.height / 50

        circumferences = {}
        for height in heights:
            mask = np.abs(self.vertices[:, 1] - height) < slice_thickness
            if mask.sum() < 10:
                continue

            points_2d = self.vertices[mask][:, [0, 2]]

            try:
                from scipy.spatial import ConvexHull
                hull = ConvexHull(points_2d)
                circumferences[height] = hull.area  # Perimeter in 2D
            except:
                continue

        if not circumferences:
            return

        heights = np.array(sorted(circumferences.keys()))
        circs = np.array([circumferences[h] for h in heights])

        self.measurements.total_height = self.height

        if self.garment_type == GarmentType.PANTS:
            # Waist: top of garment
            waist_idx = -3  # Near top
            self.measurements.waist_circumference = circs[waist_idx]

            # Hip: maximum circumference in upper half
            upper_half = circs[len(circs) // 2:]
            hip_idx = len(circs) // 2 + np.argmax(upper_half)
            self.measurements.hip_circumference = circs[hip_idx]

            # Find where legs split (sharp drop in circumference)
            circ_diff = np.diff(circs)
            split_candidates = np.where(circ_diff < -circ_diff.std() * 2)[0]

            if len(split_candidates) > 0:
                split_idx = split_candidates[-1]  # Highest significant drop
                crotch_height = heights[split_idx]

                # Rise: waist to crotch
                waist_height = heights[waist_idx]
                self.measurements.front_rise = waist_height - crotch_height
                self.measurements.back_rise = waist_height - crotch_height

                # Inseam: crotch to hem
                hem_height = heights[2]
                self.measurements.inseam_length = crotch_height - hem_height

                # Outseam: waist to hem
                self.measurements.outseam_length = waist_height - hem_height

                # Thigh: just below crotch (single leg)
                thigh_height = crotch_height - 50
                thigh_idx = np.searchsorted(heights, thigh_height)
                if 0 < thigh_idx < len(circs):
                    # Approximate single leg circumference
                    self.measurements.thigh_circumference = circs[thigh_idx] / 2

            # Knee: middle of leg
            knee_height = self.min_y + (crotch_height - self.min_y) * 0.5
            knee_idx = np.searchsorted(heights, knee_height)
            if 0 < knee_idx < len(circs):
                self.measurements.knee_circumference = circs[knee_idx] / 2

            # Ankle: near hem
            ankle_idx = 3
            self.measurements.ankle_circumference = circs[ankle_idx] / 2

        elif self.garment_type in [GarmentType.SHIRT, GarmentType.DRESS]:
            # Chest: maximum circumference
            self.measurements.chest_circumference = circs.max()

            # Waist: minimum in middle
            mid_start = len(circs) // 3
            mid_end = 2 * len(circs) // 3
            mid_circs = circs[mid_start:mid_end]
            waist_idx = mid_start + np.argmin(mid_circs)
            self.measurements.waist_circumference = circs[waist_idx]

            # Body length
            self.measurements.body_length = self.height

    def _segment_pattern_pieces(self):
        """
        Segment the garment mesh into pattern pieces using seams as boundaries.

        This is a simplified version - full implementation would use seams
        to cut the mesh and then UV unwrap each piece.
        """
        # For now, create basic pattern pieces based on garment type
        if self.garment_type == GarmentType.PANTS:
            # Pants typically have: front left/right, back left/right, waistband
            self._create_pants_pieces()
        elif self.garment_type == GarmentType.SHIRT:
            # Shirt: front, back, sleeves
            self._create_shirt_pieces()
        else:
            # Single piece fallback
            self._create_single_piece()

    def _create_pants_pieces(self):
        """Create pattern pieces for pants"""
        # Split mesh by X coordinate and height
        center_x = self.vertices[:, 0].mean()
        crotch_height = self.min_y + self.height * 0.4  # Approximate

        # Front left leg
        mask = (self.vertices[:, 0] < center_x) & \
               (self.vertices[:, 1] < crotch_height) & \
               (self.vertices[:, 2] > 0)

        if mask.sum() > 10:
            piece = self._create_piece_from_mask(mask, "front_left_leg",
                                                  ["inseam", "outseam", "hem"])
            if piece:
                self.pattern_pieces.append(piece)

        # Front right leg
        mask = (self.vertices[:, 0] >= center_x) & \
               (self.vertices[:, 1] < crotch_height) & \
               (self.vertices[:, 2] > 0)

        if mask.sum() > 10:
            piece = self._create_piece_from_mask(mask, "front_right_leg",
                                                  ["inseam", "outseam", "hem"])
            if piece:
                self.pattern_pieces.append(piece)

        # Back left leg
        mask = (self.vertices[:, 0] < center_x) & \
               (self.vertices[:, 1] < crotch_height) & \
               (self.vertices[:, 2] <= 0)

        if mask.sum() > 10:
            piece = self._create_piece_from_mask(mask, "back_left_leg",
                                                  ["inseam", "outseam", "hem"])
            if piece:
                self.pattern_pieces.append(piece)

        # Back right leg
        mask = (self.vertices[:, 0] >= center_x) & \
               (self.vertices[:, 1] < crotch_height) & \
               (self.vertices[:, 2] <= 0)

        if mask.sum() > 10:
            piece = self._create_piece_from_mask(mask, "back_right_leg",
                                                  ["inseam", "outseam", "hem"])
            if piece:
                self.pattern_pieces.append(piece)

        # Seat/crotch area
        mask = (self.vertices[:, 1] >= crotch_height) & \
               (self.vertices[:, 1] < self.min_y + self.height * 0.7)

        if mask.sum() > 10:
            piece = self._create_piece_from_mask(mask, "seat",
                                                  ["waistband", "crotch"])
            if piece:
                self.pattern_pieces.append(piece)

        # Waistband
        mask = self.vertices[:, 1] >= self.min_y + self.height * 0.9

        if mask.sum() > 10:
            piece = self._create_piece_from_mask(mask, "waistband",
                                                  ["waistband_top", "waistband_bottom"])
            if piece:
                self.pattern_pieces.append(piece)

    def _create_shirt_pieces(self):
        """Create pattern pieces for shirt"""
        center_z = self.vertices[:, 2].mean()

        # Front
        mask = self.vertices[:, 2] > center_z
        if mask.sum() > 10:
            piece = self._create_piece_from_mask(mask, "front",
                                                  ["shoulder", "side_seam", "hem"])
            if piece:
                self.pattern_pieces.append(piece)

        # Back
        mask = self.vertices[:, 2] <= center_z
        if mask.sum() > 10:
            piece = self._create_piece_from_mask(mask, "back",
                                                  ["shoulder", "side_seam", "hem"])
            if piece:
                self.pattern_pieces.append(piece)

    def _create_single_piece(self):
        """Create a single pattern piece from the whole mesh"""
        mask = np.ones(len(self.vertices), dtype=bool)
        piece = self._create_piece_from_mask(mask, "main", ["seam"])
        if piece:
            self.pattern_pieces.append(piece)

    def _create_piece_from_mask(self, vertex_mask: np.ndarray,
                                 name: str, seams: List[str]) -> Optional[PatternPiece]:
        """
        Create a pattern piece from a vertex mask.

        Performs simple UV unwrapping by projecting onto a plane.
        """
        indices = np.where(vertex_mask)[0]
        if len(indices) < 4:
            return None

        vertices_3d = self.vertices[indices]

        # Simple UV unwrap: project onto best-fit plane
        center = vertices_3d.mean(axis=0)
        centered = vertices_3d - center

        # PCA to find projection plane
        cov = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # Project onto plane formed by two largest eigenvectors
        order = np.argsort(eigenvalues)[::-1]
        u_axis = eigenvectors[:, order[0]]
        v_axis = eigenvectors[:, order[1]]

        vertices_2d = np.column_stack([
            np.dot(centered, u_axis),
            np.dot(centered, v_axis)
        ])

        # Find boundary vertices (simplified)
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(vertices_2d)
            boundary = vertices_2d[hull.vertices]
        except:
            boundary = vertices_2d[:4]  # Fallback

        # Compute area
        area = self._polygon_area(boundary)

        # Find faces that use these vertices
        index_set = set(indices)
        piece_faces = []
        for face_idx, face in enumerate(self.faces):
            if all(v in index_set for v in face):
                piece_faces.append(face)

        return PatternPiece(
            name=name,
            vertices_3d=vertices_3d,
            vertices_2d=vertices_2d,
            faces=np.array(piece_faces) if piece_faces else np.array([]),
            boundary=boundary,
            area=area,
            seams=seams
        )

    def _polygon_area(self, points: np.ndarray) -> float:
        """Compute area of a 2D polygon"""
        n = len(points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i, 0] * points[j, 1]
            area -= points[j, 0] * points[i, 1]
        return abs(area) / 2.0

    def to_dict(self) -> Dict[str, Any]:
        """Export garment model to dictionary for API responses"""
        return {
            'garment_type': self.garment_type.value,
            'seams': [s.to_dict() for s in self.seams],
            'pattern_pieces': [p.to_dict() for p in self.pattern_pieces],
            'measurements': self.measurements.to_dict(),
            'bounds': {
                'min_y': float(self.min_y),
                'max_y': float(self.max_y),
                'height': float(self.height)
            }
        }


def analyze_garment_mesh(vertices: np.ndarray, faces: np.ndarray,
                          garment_type: str = None) -> Dict[str, Any]:
    """
    Convenience function for API use.

    Args:
        vertices: Nx3 array of vertex positions
        faces: Mx3 array of face indices
        garment_type: Optional garment type override

    Returns:
        Dict with seams, pattern pieces, and measurements
    """
    model = GarmentModel(vertices, faces)
    model.analyze(garment_type)

    return model.to_dict()
