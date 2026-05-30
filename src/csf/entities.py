from dataclasses import dataclass
from typing import Optional, Tuple
from collections.abc import Mapping
from . import _tol
class CSFError(ValueError):
    pass

# -------------------------
# Geometry primitives
# -------------------------

@dataclass(frozen=True)
class Pt:
    x: float
    y: float

    def lerp(self, other: "Pt", z_real: float, length: float) -> "Pt": 
            """
            Calculates the interpolated point at a specific distance using slopes.
            
            Args:
                self start point
                other (Pt): Ending point (top).
                z_real (float): relative Distance from the starting point (0 to length).
                length (float): Total vertical length of the segment.
            """
         
            # Avoid division by zero
            if abs(length) < _tol.EPS_L:
                return self

            # 1. Calculate the geometric slope (how much x and y change per meter)
            slope_x = (other.x - self.x) / length
            slope_y = (other.y - self.y) / length

            # 2. Add the change to the initial x and y coordinates
            # New = Initial + (Rate of change * distance)
            xr = self.x + (slope_x * z_real)
            yr = self.y + (slope_y * z_real) 
            
            return Pt( 
                x = xr, 
                y = yr  
            )

@dataclass(frozen=True)
class Polygon:
    vertices: Tuple[Pt, ...]
    weight: Optional[float] = None
    name: str = ""
    weightabs: Optional[float] = None
    shear_weight: Optional[float] = None
    shear_weightabs: Optional[float] = None
    poisson: Optional[float] = None
    def __post_init__(self) -> None:
        """
        Validation steps executed automatically after object initialization.
        """
        # 1. Check for minimum number of vertices
        if len(self.vertices) < 3:
            raise ValueError(f"Polygon '{self.name}' must have at least 3 vertices.")

        # 2. Check for Counter-Clockwise (CCW) orientation
        # We use the Shoelace formula to calculate the signed area (a2).
        # A positive result indicates CCW, a negative result indicates CW.
        verts = self.vertices
        n = len(verts)
        a2 = 0.0
        for i in range(n):
            x0, y0 = verts[i].x, verts[i].y
            x1, y1 = verts[(i + 1) % n].x, verts[(i + 1) % n].y
            a2 += (x0 * y1 - x1 * y0)
        
        # If a2 is negative, the winding order is Clockwise (CW).
        if a2 <= 0:
            raise ValueError(
                f"GEOMETRIC ERROR:: Polygon '{self.name}' has area {a2}. "
                f"Polygons must have a positive area and be defined in Counter-Clockwise (CCW) order. "
                f"An area of 0 means the polygon is degenerate (e.g., only 2 sides)."
            )
        
        if abs(a2) < _tol.EPS_A: # Check if the area is practically zero
                raise ValueError(
                    f"GEOMETRIC ERROR: Polygon '{self.name}' has zero area (degenerate polygon). "
                    f"A polygon must have at least 3 non-collinear vertices (it cannot have only 2 sides)."
                )        
        # GEOMETRIC INTEGRITY CHECK
        if a2 < _tol.EPS_A:  # Covers both negative area and zero area
            if a2 < 0:
                # Case: Clockwise (CW) order
                raise ValueError(
                    f"GEOMETRIC ERROR: Polygon '{self.name}' is defined in Clockwise (CW) order. "
                    f"All polygons must be Counter-Clockwise (CCW). "
                    f"Use weight={self.weight} for voids instead of flipping vertices."
                )
            else:
                # Case: Zero Area (2 sides or collinear points)
                raise ValueError(
                    f"GEOMETRIC ERROR: Polygon '{self.name}' has zero area (degenerate). "
                    f"A polygon must have at least 3 non-collinear vertices to enclose an area."
                )
        # Default shear weight follows the standard weight unless explicitly set.
        if self.shear_weight is None:
            object.__setattr__(self, "shear_weight", self.weight)
            


@dataclass(frozen=True)
class Section:
    polygons: Tuple[Polygon, ...]
    z: float

    def __post_init__(self) -> None:
        if isinstance(self.polygons, Polygon):
            raise TypeError(
                "Section.polygons must be a tuple of Polygon. "
                "For a single polygon, use (poly,) not (poly,)."
            )

        if isinstance(self.polygons, Mapping):
            raise TypeError(
                "Section.polygons must be a tuple of Polygon, not a mapping/dict."
            )

        if not isinstance(self.polygons, tuple):
            raise TypeError(
                "Section.polygons must be a tuple of Polygon."
            )

        if len(self.polygons) == 0:
            raise ValueError(
                "Section must contain at least one Polygon."
            )

        for p in self.polygons:
            if not isinstance(p, Polygon):
                raise TypeError(
                    "All elements of Section.polygons must be Polygon."
                )

        seen_names = set()

        for i, poly in enumerate(self.polygons):
            if not poly.name or not poly.name.strip():
                raise ValueError(
                    f"VALIDATION ERROR: Polygon at index {i} in section at Z={self.z} "
                    f"has an empty or invalid name. All polygons must have a unique name."
                )

            if poly.name in seen_names:
                raise ValueError(
                    f"VALIDATION ERROR: Duplicate polygon name '{poly.name}' detected "
                    f"in section at Z={self.z}. Each polygon within a section must have a unique name."
                )

            seen_names.add(poly.name)
