"""
Mesh Processing Module for Make It Cunt v3.0

Handles 3D scan import, cleaning, and alignment for body and garment meshes.
Designed for Revopoint Inspire scanner output (PLY, OBJ, STL via Revo Scan 5).
Supports 0.2mm accuracy scans with ~0.3mm point spacing.

Dependencies: pymeshlab, open3d, trimesh, numpy
"""

import os
import tempfile
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum
import numpy as np

try:
    import pymeshlab
    PYMESHLAB_AVAILABLE = True
except ImportError:
    PYMESHLAB_AVAILABLE = False
    print("Warning: pymeshlab not installed. Some cleaning features unavailable.")

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    print("Warning: open3d not installed. Alignment features unavailable.")

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    print("Warning: trimesh not installed. Some mesh operations unavailable.")


class MeshType(Enum):
    """Type of mesh being processed"""
    BODY = "body"
    GARMENT = "garment"
    UNKNOWN = "unknown"


class MeshUnit(Enum):
    """Units of the mesh coordinates"""
    MILLIMETERS = "mm"
    CENTIMETERS = "cm"
    METERS = "m"
    INCHES = "in"


@dataclass
class MeshStats:
    """Statistics about a processed mesh"""
    vertex_count: int
    face_count: int
    bounding_box: Tuple[np.ndarray, np.ndarray]  # min, max corners
    center: np.ndarray
    dimensions: np.ndarray  # width, height, depth
    is_watertight: bool
    has_normals: bool
    unit: MeshUnit = MeshUnit.MILLIMETERS

    def to_dict(self) -> Dict[str, Any]:
        return {
            'vertex_count': self.vertex_count,
            'face_count': self.face_count,
            'bounding_box': {
                'min': self.bounding_box[0].tolist(),
                'max': self.bounding_box[1].tolist()
            },
            'center': self.center.tolist(),
            'dimensions': self.dimensions.tolist(),
            'is_watertight': self.is_watertight,
            'has_normals': self.has_normals,
            'unit': self.unit.value
        }


@dataclass
class ProcessedMesh:
    """Container for a processed mesh with metadata"""
    mesh: Any  # trimesh.Trimesh or similar
    mesh_type: MeshType
    stats: MeshStats
    vertices: np.ndarray
    faces: np.ndarray
    normals: Optional[np.ndarray] = None
    original_filename: str = ""
    processing_log: List[str] = field(default_factory=list)

    def log(self, message: str):
        self.processing_log.append(message)


class MeshProcessor:
    """
    Main class for processing 3D scans.

    Workflow:
    1. Load mesh from file (PLY, OBJ, STL)
    2. Clean mesh (remove noise, fill holes, smooth)
    3. Orient mesh (body upright, garment on form)
    4. Compute statistics and prepare for analysis
    """

    def __init__(self, target_unit: MeshUnit = MeshUnit.MILLIMETERS):
        self.target_unit = target_unit
        self._check_dependencies()

    def _check_dependencies(self):
        """Check which processing backends are available"""
        self.backends = {
            'pymeshlab': PYMESHLAB_AVAILABLE,
            'open3d': OPEN3D_AVAILABLE,
            'trimesh': TRIMESH_AVAILABLE
        }

        if not any(self.backends.values()):
            raise RuntimeError("No mesh processing backend available. Install trimesh, open3d, or pymeshlab.")

    def load_mesh(self, file_path: str = None, file_bytes: bytes = None,
                  filename: str = None) -> ProcessedMesh:
        """
        Load a mesh from file path or bytes.

        Args:
            file_path: Path to mesh file (PLY, OBJ, STL)
            file_bytes: Raw file bytes (for uploaded files)
            filename: Original filename (for format detection when using bytes)

        Returns:
            ProcessedMesh object with loaded data
        """
        if file_path:
            filename = os.path.basename(file_path)
        elif file_bytes and filename:
            # Write to temp file for loading
            suffix = os.path.splitext(filename)[1].lower()
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(file_bytes)
                file_path = f.name
        else:
            raise ValueError("Must provide either file_path or (file_bytes and filename)")

        # Detect format
        ext = os.path.splitext(file_path)[1].lower()

        # Load with trimesh (most flexible)
        if TRIMESH_AVAILABLE:
            mesh = trimesh.load(file_path, force='mesh')

            vertices = np.array(mesh.vertices)
            faces = np.array(mesh.faces)
            normals = np.array(mesh.vertex_normals) if mesh.vertex_normals is not None else None

            # Compute stats
            bbox_min = vertices.min(axis=0)
            bbox_max = vertices.max(axis=0)
            center = (bbox_min + bbox_max) / 2
            dimensions = bbox_max - bbox_min

            stats = MeshStats(
                vertex_count=len(vertices),
                face_count=len(faces),
                bounding_box=(bbox_min, bbox_max),
                center=center,
                dimensions=dimensions,
                is_watertight=mesh.is_watertight,
                has_normals=normals is not None,
                unit=self._detect_units(dimensions)
            )

            processed = ProcessedMesh(
                mesh=mesh,
                mesh_type=MeshType.UNKNOWN,
                stats=stats,
                vertices=vertices,
                faces=faces,
                normals=normals,
                original_filename=filename
            )
            processed.log(f"Loaded mesh from {filename}: {stats.vertex_count} vertices, {stats.face_count} faces")

            return processed

        elif OPEN3D_AVAILABLE:
            mesh = o3d.io.read_triangle_mesh(file_path)
            mesh.compute_vertex_normals()

            vertices = np.asarray(mesh.vertices)
            faces = np.asarray(mesh.triangles)
            normals = np.asarray(mesh.vertex_normals)

            bbox_min = vertices.min(axis=0)
            bbox_max = vertices.max(axis=0)
            center = (bbox_min + bbox_max) / 2
            dimensions = bbox_max - bbox_min

            stats = MeshStats(
                vertex_count=len(vertices),
                face_count=len(faces),
                bounding_box=(bbox_min, bbox_max),
                center=center,
                dimensions=dimensions,
                is_watertight=mesh.is_watertight(),
                has_normals=True,
                unit=self._detect_units(dimensions)
            )

            processed = ProcessedMesh(
                mesh=mesh,
                mesh_type=MeshType.UNKNOWN,
                stats=stats,
                vertices=vertices,
                faces=faces,
                normals=normals,
                original_filename=filename
            )
            processed.log(f"Loaded mesh from {filename} using Open3D")

            return processed

        else:
            raise RuntimeError("No mesh loading backend available")

    def _detect_units(self, dimensions: np.ndarray) -> MeshUnit:
        """
        Attempt to detect mesh units based on typical human body dimensions.

        Human body approximate dimensions:
        - Height: ~1700mm, ~170cm, ~1.7m, ~67in
        - Width: ~500mm, ~50cm, ~0.5m, ~20in
        """
        max_dim = dimensions.max()

        if max_dim > 500:  # Likely millimeters
            return MeshUnit.MILLIMETERS
        elif max_dim > 50:  # Likely centimeters or inches
            return MeshUnit.CENTIMETERS
        elif max_dim > 0.5:  # Likely meters
            return MeshUnit.METERS
        else:
            return MeshUnit.MILLIMETERS  # Default assumption

    def clean_mesh(self, processed: ProcessedMesh,
                   remove_noise: bool = True,
                   fill_holes: bool = True,
                   smooth: bool = True,
                   decimate_target: Optional[int] = None) -> ProcessedMesh:
        """
        Clean a mesh by removing noise, filling holes, and smoothing.

        Args:
            processed: ProcessedMesh to clean
            remove_noise: Remove small disconnected components
            fill_holes: Fill holes in the mesh
            smooth: Apply light smoothing
            decimate_target: Target vertex count for decimation (None to skip)

        Returns:
            Cleaned ProcessedMesh
        """
        if PYMESHLAB_AVAILABLE:
            return self._clean_with_pymeshlab(processed, remove_noise, fill_holes, smooth, decimate_target)
        elif TRIMESH_AVAILABLE:
            return self._clean_with_trimesh(processed, remove_noise, fill_holes, smooth)
        else:
            processed.log("Warning: No cleaning backend available, returning as-is")
            return processed

    def _clean_with_pymeshlab(self, processed: ProcessedMesh,
                               remove_noise: bool, fill_holes: bool,
                               smooth: bool, decimate_target: Optional[int]) -> ProcessedMesh:
        """Clean mesh using PyMeshLab"""
        ms = pymeshlab.MeshSet()

        # Create mesh from arrays
        mesh = pymeshlab.Mesh(processed.vertices, processed.faces)
        ms.add_mesh(mesh)

        if remove_noise:
            # Remove small disconnected components (keep largest)
            ms.compute_selection_by_small_disconnected_components_per_face(nbfaceratio=0.1)
            ms.meshing_remove_selected_faces()
            ms.meshing_remove_unreferenced_vertices()
            processed.log("Removed small disconnected components")

        if fill_holes:
            # Fill holes
            ms.meshing_close_holes(maxholesize=100)
            processed.log("Filled holes")

        if smooth:
            # Light Laplacian smoothing
            ms.apply_coord_laplacian_smoothing(stepsmoothnum=2)
            processed.log("Applied Laplacian smoothing")

        if decimate_target and processed.stats.vertex_count > decimate_target:
            # Decimate to target vertex count
            ms.meshing_decimation_quadric_edge_collapse(targetfacenum=decimate_target)
            processed.log(f"Decimated to ~{decimate_target} vertices")

        # Extract cleaned mesh
        cleaned = ms.current_mesh()
        vertices = cleaned.vertex_matrix()
        faces = cleaned.face_matrix()
        normals = cleaned.vertex_normal_matrix() if cleaned.has_vertex_normal() else None

        # Update stats
        bbox_min = vertices.min(axis=0)
        bbox_max = vertices.max(axis=0)
        center = (bbox_min + bbox_max) / 2
        dimensions = bbox_max - bbox_min

        processed.vertices = vertices
        processed.faces = faces
        processed.normals = normals
        processed.stats = MeshStats(
            vertex_count=len(vertices),
            face_count=len(faces),
            bounding_box=(bbox_min, bbox_max),
            center=center,
            dimensions=dimensions,
            is_watertight=processed.stats.is_watertight,  # May have changed
            has_normals=normals is not None,
            unit=processed.stats.unit
        )

        # Update trimesh object if available
        if TRIMESH_AVAILABLE:
            processed.mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

        return processed

    def _clean_with_trimesh(self, processed: ProcessedMesh,
                            remove_noise: bool, fill_holes: bool,
                            smooth: bool) -> ProcessedMesh:
        """Clean mesh using trimesh"""
        mesh = processed.mesh

        if remove_noise:
            # Keep only largest connected component
            components = mesh.split(only_watertight=False)
            if len(components) > 1:
                largest = max(components, key=lambda m: len(m.vertices))
                mesh = largest
                processed.log(f"Kept largest component of {len(components)} components")

        if fill_holes:
            # Fill holes by adding faces
            mesh.fill_holes()
            processed.log("Filled holes")

        if smooth:
            # Laplacian smoothing
            trimesh.smoothing.filter_laplacian(mesh, iterations=2)
            processed.log("Applied Laplacian smoothing")

        # Update processed mesh
        processed.mesh = mesh
        processed.vertices = np.array(mesh.vertices)
        processed.faces = np.array(mesh.faces)
        processed.normals = np.array(mesh.vertex_normals)

        # Update stats
        bbox_min = processed.vertices.min(axis=0)
        bbox_max = processed.vertices.max(axis=0)
        center = (bbox_min + bbox_max) / 2
        dimensions = bbox_max - bbox_min

        processed.stats = MeshStats(
            vertex_count=len(processed.vertices),
            face_count=len(processed.faces),
            bounding_box=(bbox_min, bbox_max),
            center=center,
            dimensions=dimensions,
            is_watertight=mesh.is_watertight,
            has_normals=True,
            unit=processed.stats.unit
        )

        return processed

    def orient_body(self, processed: ProcessedMesh) -> ProcessedMesh:
        """
        Orient a body mesh to standard position:
        - Centered at origin
        - Standing upright (Y-up or Z-up depending on convention)
        - Facing forward (negative Z or positive Y)

        Uses PCA to find principal axes and heuristics for body orientation.
        """
        vertices = processed.vertices.copy()

        # Center at origin
        center = vertices.mean(axis=0)
        vertices -= center
        processed.log(f"Centered mesh at origin (shifted by {center})")

        # PCA to find principal axes
        cov = np.cov(vertices.T)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # Sort by eigenvalue (largest = longest axis = height for body)
        order = np.argsort(eigenvalues)[::-1]
        eigenvectors = eigenvectors[:, order]

        # The longest axis should be vertical (Y-up convention)
        # Rotate to align principal axis with Y
        rotation = eigenvectors.T
        vertices = vertices @ rotation.T
        processed.log("Aligned principal axis with Y (height)")

        # Ensure Y is pointing up (feet at bottom)
        # The bottom of the body should have more vertices close together (feet)
        y_coords = vertices[:, 1]
        bottom_vertices = vertices[y_coords < np.percentile(y_coords, 10)]
        top_vertices = vertices[y_coords > np.percentile(y_coords, 90)]

        # Feet are typically narrower than head, so bottom should have smaller spread
        bottom_spread = np.std(bottom_vertices[:, [0, 2]])  # X-Z spread
        top_spread = np.std(top_vertices[:, [0, 2]])

        if bottom_spread > top_spread:
            # Flip - head is at bottom
            vertices[:, 1] *= -1
            processed.log("Flipped mesh (was upside down)")

        # Update mesh
        processed.vertices = vertices
        if processed.normals is not None:
            processed.normals = processed.normals @ rotation.T

        if TRIMESH_AVAILABLE:
            processed.mesh = trimesh.Trimesh(vertices=vertices, faces=processed.faces)

        processed.mesh_type = MeshType.BODY

        # Update stats
        bbox_min = vertices.min(axis=0)
        bbox_max = vertices.max(axis=0)
        processed.stats = MeshStats(
            vertex_count=len(vertices),
            face_count=len(processed.faces),
            bounding_box=(bbox_min, bbox_max),
            center=vertices.mean(axis=0),
            dimensions=bbox_max - bbox_min,
            is_watertight=processed.stats.is_watertight,
            has_normals=processed.normals is not None,
            unit=processed.stats.unit
        )

        return processed

    def orient_garment(self, processed: ProcessedMesh,
                       garment_type: str = "pants") -> ProcessedMesh:
        """
        Orient a garment mesh for analysis.

        For garments on dress form: orient similar to body
        For flat garments: orient with longest dimension as height

        Args:
            processed: Garment mesh
            garment_type: Type of garment ("pants", "shirt", "dress", etc.)
        """
        vertices = processed.vertices.copy()

        # Center at origin
        center = vertices.mean(axis=0)
        vertices -= center
        processed.log(f"Centered garment at origin")

        # For garments on dress form, use same orientation as body
        # PCA alignment
        cov = np.cov(vertices.T)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        order = np.argsort(eigenvalues)[::-1]
        eigenvectors = eigenvectors[:, order]

        rotation = eigenvectors.T
        vertices = vertices @ rotation.T
        processed.log("Aligned garment principal axis with Y")

        # Update mesh
        processed.vertices = vertices
        if processed.normals is not None:
            processed.normals = processed.normals @ rotation.T

        if TRIMESH_AVAILABLE:
            processed.mesh = trimesh.Trimesh(vertices=vertices, faces=processed.faces)

        processed.mesh_type = MeshType.GARMENT

        # Update stats
        bbox_min = vertices.min(axis=0)
        bbox_max = vertices.max(axis=0)
        processed.stats = MeshStats(
            vertex_count=len(vertices),
            face_count=len(processed.faces),
            bounding_box=(bbox_min, bbox_max),
            center=vertices.mean(axis=0),
            dimensions=bbox_max - bbox_min,
            is_watertight=processed.stats.is_watertight,
            has_normals=processed.normals is not None,
            unit=processed.stats.unit
        )

        return processed

    def convert_units(self, processed: ProcessedMesh,
                      target_unit: MeshUnit) -> ProcessedMesh:
        """
        Convert mesh coordinates to target units.
        """
        current = processed.stats.unit

        # Conversion factors to millimeters
        to_mm = {
            MeshUnit.MILLIMETERS: 1.0,
            MeshUnit.CENTIMETERS: 10.0,
            MeshUnit.METERS: 1000.0,
            MeshUnit.INCHES: 25.4
        }

        # Convert current → mm → target
        scale = to_mm[current] / to_mm[target_unit]

        if scale != 1.0:
            processed.vertices *= scale

            # Update stats
            bbox_min = processed.vertices.min(axis=0)
            bbox_max = processed.vertices.max(axis=0)
            processed.stats = MeshStats(
                vertex_count=processed.stats.vertex_count,
                face_count=processed.stats.face_count,
                bounding_box=(bbox_min, bbox_max),
                center=processed.vertices.mean(axis=0),
                dimensions=bbox_max - bbox_min,
                is_watertight=processed.stats.is_watertight,
                has_normals=processed.stats.has_normals,
                unit=target_unit
            )

            if TRIMESH_AVAILABLE:
                processed.mesh = trimesh.Trimesh(
                    vertices=processed.vertices,
                    faces=processed.faces
                )

            processed.log(f"Converted from {current.value} to {target_unit.value} (scale: {scale})")

        return processed

    def align_meshes(self, body: ProcessedMesh,
                     garment: ProcessedMesh) -> Tuple[ProcessedMesh, ProcessedMesh]:
        """
        Align body and garment meshes in the same coordinate space.

        Uses ICP (Iterative Closest Point) if Open3D available,
        otherwise uses bounding box alignment.

        Returns:
            Tuple of (aligned_body, aligned_garment)
        """
        # Ensure same units
        if body.stats.unit != garment.stats.unit:
            garment = self.convert_units(garment, body.stats.unit)

        # Simple bounding box alignment for now
        # Align garment center to body center
        body_center = body.stats.center
        garment_center = garment.stats.center

        offset = body_center - garment_center
        garment.vertices += offset

        if TRIMESH_AVAILABLE:
            garment.mesh = trimesh.Trimesh(
                vertices=garment.vertices,
                faces=garment.faces
            )

        # Update garment stats
        bbox_min = garment.vertices.min(axis=0)
        bbox_max = garment.vertices.max(axis=0)
        garment.stats = MeshStats(
            vertex_count=garment.stats.vertex_count,
            face_count=garment.stats.face_count,
            bounding_box=(bbox_min, bbox_max),
            center=garment.vertices.mean(axis=0),
            dimensions=bbox_max - bbox_min,
            is_watertight=garment.stats.is_watertight,
            has_normals=garment.stats.has_normals,
            unit=garment.stats.unit
        )

        body.log("Aligned with garment mesh")
        garment.log(f"Aligned with body mesh (offset: {offset})")

        return body, garment

    def export_mesh(self, processed: ProcessedMesh,
                    output_path: str,
                    format: str = "ply") -> str:
        """
        Export processed mesh to file.

        Args:
            processed: Mesh to export
            output_path: Output file path
            format: Output format (ply, obj, stl)

        Returns:
            Path to exported file
        """
        if TRIMESH_AVAILABLE:
            processed.mesh.export(output_path, file_type=format)
            processed.log(f"Exported to {output_path}")
            return output_path
        elif OPEN3D_AVAILABLE:
            mesh = o3d.geometry.TriangleMesh()
            mesh.vertices = o3d.utility.Vector3dVector(processed.vertices)
            mesh.triangles = o3d.utility.Vector3iVector(processed.faces)
            if processed.normals is not None:
                mesh.vertex_normals = o3d.utility.Vector3dVector(processed.normals)
            o3d.io.write_triangle_mesh(output_path, mesh)
            processed.log(f"Exported to {output_path}")
            return output_path
        else:
            raise RuntimeError("No export backend available")


# Convenience functions for API use
def process_body_scan(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Process a body scan from uploaded file.

    Returns dict with mesh stats and processing info.
    """
    processor = MeshProcessor()
    mesh = processor.load_mesh(file_bytes=file_bytes, filename=filename)
    mesh = processor.clean_mesh(mesh)
    mesh = processor.orient_body(mesh)

    return {
        'success': True,
        'mesh_type': 'body',
        'stats': mesh.stats.to_dict(),
        'processing_log': mesh.processing_log
    }


def process_garment_scan(file_bytes: bytes, filename: str,
                         garment_type: str = "pants") -> Dict[str, Any]:
    """
    Process a garment scan from uploaded file.

    Returns dict with mesh stats and processing info.
    """
    processor = MeshProcessor()
    mesh = processor.load_mesh(file_bytes=file_bytes, filename=filename)
    mesh = processor.clean_mesh(mesh)
    mesh = processor.orient_garment(mesh, garment_type)

    return {
        'success': True,
        'mesh_type': 'garment',
        'garment_type': garment_type,
        'stats': mesh.stats.to_dict(),
        'processing_log': mesh.processing_log
    }
