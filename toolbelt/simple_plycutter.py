import math
import random
import struct
import sys

# Global plycutter instance
plycutter = None

def initialize_plycutter(thickness, min_finger_width, max_finger_width, 
                       support_radius, final_dilation, random_seed):
    global plycutter
    plycutter = SimplePlycutter(
        thickness=thickness,
        min_finger_width=min_finger_width,
        max_finger_width=max_finger_width,
        support_radius=support_radius,
        final_dilation=final_dilation,
        random_seed=random_seed
    )
    return "SimplePlycutter initialized successfully"

def process_stl_file(stl_data):
    global plycutter
    if plycutter is None:
        return "Error: SimplePlycutter not initialized"
    
    dxf_output = plycutter.process_stl(stl_data)
    return dxf_output

def get_svg_preview():
    global plycutter
    if plycutter is None:
        return "<svg></svg>"
    return plycutter.get_preview_svg()

def get_logs():
    return sys.stdout.get_logs()

# Simple STL parser for binary STL files
class STLParser:
    def __init__(self):
        self.triangles = []
    
    def parse(self, data):
        try:
            # Skip header (80 bytes) and read number of triangles (4 bytes)
            header = data[:80]
            num_triangles = struct.unpack('<I', data[80:84])[0]
            print(f"STL contains {num_triangles} triangles")
            
            # Each triangle is 50 bytes (12 bytes for normal, 36 bytes for vertices, 2 bytes for attribute)
            offset = 84
            for i in range(num_triangles):
                if offset + 50 > len(data):
                    print(f"Warning: STL file truncated at triangle {i}")
                    break
                
                # Extract normal and vertices
                normal = struct.unpack('<fff', data[offset:offset+12])
                v1 = struct.unpack('<fff', data[offset+12:offset+24])
                v2 = struct.unpack('<fff', data[offset+24:offset+36])
                v3 = struct.unpack('<fff', data[offset+36:offset+48])
                
                self.triangles.append({
                    'normal': normal,
                    'vertices': [v1, v2, v3]
                })
                
                offset += 50
            
            print(f"Successfully parsed {len(self.triangles)} triangles")
            return True
        except Exception as e:
            print(f"Error parsing STL: {e}")
            # Fall back to a mock data if parsing fails
            self._generate_mock_data()
            return False
    
    def _generate_mock_data(self):
        print("Generating mock triangles for demonstration")
        # Create a simple box
        size = 100
        thickness = 6
        
        # Create a box with 6 faces, each with 2 triangles
        # Front face
        self.triangles.append({
            'normal': (0, 0, 1),
            'vertices': [(0, 0, thickness), (size, 0, thickness), (size, size, thickness)]
        })
        self.triangles.append({
            'normal': (0, 0, 1),
            'vertices': [(0, 0, thickness), (size, size, thickness), (0, size, thickness)]
        })
        
        # Back face
        self.triangles.append({
            'normal': (0, 0, -1),
            'vertices': [(0, 0, 0), (size, size, 0), (size, 0, 0)]
        })
        self.triangles.append({
            'normal': (0, 0, -1),
            'vertices': [(0, 0, 0), (0, size, 0), (size, size, 0)]
        })
        
        # Top face
        self.triangles.append({
            'normal': (0, 1, 0),
            'vertices': [(0, size, 0), (size, size, 0), (size, size, thickness)]
        })
        self.triangles.append({
            'normal': (0, 1, 0),
            'vertices': [(0, size, 0), (size, size, thickness), (0, size, thickness)]
        })
        
        # Bottom face
        self.triangles.append({
            'normal': (0, -1, 0),
            'vertices': [(0, 0, 0), (size, 0, thickness), (size, 0, 0)]
        })
        self.triangles.append({
            'normal': (0, -1, 0),
            'vertices': [(0, 0, 0), (0, 0, thickness), (size, 0, thickness)]
        })
        
        # Left face
        self.triangles.append({
            'normal': (-1, 0, 0),
            'vertices': [(0, 0, 0), (0, size, 0), (0, size, thickness)]
        })
        self.triangles.append({
            'normal': (-1, 0, 0),
            'vertices': [(0, 0, 0), (0, size, thickness), (0, 0, thickness)]
        })
        
        # Right face
        self.triangles.append({
            'normal': (1, 0, 0),
            'vertices': [(size, 0, 0), (size, size, thickness), (size, size, 0)]
        })
        self.triangles.append({
            'normal': (1, 0, 0),
            'vertices': [(size, 0, 0), (size, 0, thickness), (size, size, thickness)]
        })

# Simple Plycutter implementation
class SimplePlycutter:
    def __init__(self, thickness=6.0, min_finger_width=3.0, max_finger_width=5.0, 
                support_radius=12.0, final_dilation=0.05, random_seed=42):
        self.thickness = thickness
        self.min_finger_width = min_finger_width
        self.max_finger_width = max_finger_width
        self.support_radius = support_radius
        self.final_dilation = final_dilation
        self.random_seed = random_seed
        random.seed(random_seed)
        self.sheets = []
        print(f"Initialized SimplePlycutter with thickness={thickness}")
    
    def process_stl(self, stl_data):
        print(f"Processing STL data ({len(stl_data)} bytes)")
        
        # Parse the STL file
        parser = STLParser()
        success = parser.parse(stl_data)
        
        if success:
            # Analyze triangles to detect sheets
            sheets = self._detect_sheets(parser.triangles)
            self.sheets = sheets
            print(f"Detected {len(sheets)} sheets")
        
        # Generate a DXF from the sheets
        return self._generate_dxf()
    
    def _detect_sheets(self, triangles):
        # This is a simplified algorithm to detect sheets from triangles
        # In a real implementation, this would be much more sophisticated
        
        # Group triangles by normal vectors (very simplified)
        sheet_groups = {}
        for triangle in triangles:
            normal = triangle['normal']
            # Quantize normal to handle floating point imprecision
            normal_key = (round(normal[0]), round(normal[1]), round(normal[2]))
            if normal_key not in sheet_groups:
                sheet_groups[normal_key] = []
            sheet_groups[normal_key].append(triangle)
        
        # Each group of triangles with similar normals is a "sheet"
        sheets = []
        for normal, triangles in sheet_groups.items():
            # Extract outer edges for each sheet
            vertices = []
            for triangle in triangles:
                vertices.extend(triangle['vertices'])
            
            # Find approx bounding box for the sheet
            min_x = min(v[0] for v in vertices)
            max_x = max(v[0] for v in vertices)
            min_y = min(v[1] for v in vertices)
            max_y = max(v[1] for v in vertices)
            min_z = min(v[2] for v in vertices)
            max_z = max(v[2] for v in vertices)
            
            # Create a simplified representation of the sheet
            sheet = {
                'normal': normal,
                'bounds': (min_x, min_y, min_z, max_x, max_y, max_z),
                'width': max_x - min_x,
                'height': max_y - min_y,
                'depth': max_z - min_z
            }
            sheets.append(sheet)
        
        return sheets
    
    def _generate_dxf(self):
        print("Generating DXF output...")
        
        # DXF header
        dxf_header = """0
SECTION
2
HEADER
9
$ACADVER
1
AC1021
0
ENDSEC
2
TABLES
0
TABLE
2
LAYER
0
LAYER
2
0
70
0
62
7
6
CONTINUOUS
0
ENDTAB
0
ENDSEC
2
ENTITIES
"""

        # DXF footer
        dxf_footer = """0
ENDSEC
0
EOF
"""

        entities = []
        
        # If we have sheets from STL analysis, use those
        if self.sheets:
            y_offset = 0
            for i, sheet in enumerate(self.sheets):
                # Create rectangles with finger joints for each sheet
                width = max(50, min(sheet['width'], 300))  # Limit size for display
                height = max(50, min(sheet['height'], 300))
                
                # Generate finger joints based on which sheets intersect
                # This is highly simplified - real implementation would be more complex
                entities.extend(self._generate_sheet_with_joints(width, height, y_offset))
                
                y_offset += sheet_height + 20  # Add space between sheets
        else:
            # Draw sample box parts if no sheets detected
            # Bottom piece
            svg_content.append(self._generate_sheet_svg_path(width, height, padding, padding))
            svg_content.append(f'<text x="{padding + width/2}" y="{padding + height + 15}" text-anchor="middle" font-size="6">Bottom Piece</text>')
            
            # Side piece
            side_y = padding * 2 + height
            svg_content.append(self._generate_sheet_svg_path(width, height, padding, side_y))
            svg_content.append(f'<text x="{padding + width/2}" y="{side_y + height + 15}" text-anchor="middle" font-size="6">Side Piece</text>')
            
            # Another piece
            top_y = side_y + height + padding
            svg_content.append(self._generate_sheet_svg_path(height, width, padding, top_y))
            svg_content.append(f'<text x="{padding + height/2}" y="{top_y + width + 15}" text-anchor="middle" font-size="6">Top Piece</text>')
        
        # Add footer
        svg_content.append(f'<text x="{viewbox_width/2}" y="{viewbox_height - 5}" text-anchor="middle" font-size="4">SimplePlycutter Preview - Parameters: t={self.thickness}, min={self.min_finger_width}, max={self.max_finger_width}</text>')
        
        # Assemble the full SVG
        full_svg = svg_header + ''.join(svg_content) + '</svg>'
        return full_svg
    
    def _generate_sheet_svg_path(self, width, height, x_offset, y_offset):
        # Calculate number of fingers per edge
        fingers_per_edge = max(2, int((width / self.max_finger_width) / 2) * 2)
        finger_width = width / fingers_per_edge
        
        # Start the path at the top-left corner
        path = f'<path d="M {x_offset},{y_offset} '
        
        # Top edge with finger joints
        for i in range(fingers_per_edge):
            x_start = x_offset + i * finger_width
            x_end = x_offset + (i + 1) * finger_width
            
            if i % 2 == 0:  # Cut out
                path += f'L {x_start},{y_offset} L {x_start},{y_offset + self.thickness} '
                if i > 0:
                    path += f'L {x_start - finger_width},{y_offset + self.thickness} '
            else:  # Finger
                if i > 0:
                    path += f'L {x_start},{y_offset} '
        
        # Right side
        path += f'L {x_offset + width},{y_offset} L {x_offset + width},{y_offset + height} '
        
        # Bottom edge (simple)
        path += f'L {x_offset},{y_offset + height} '
        
        # Left side and close the path
        path += f'L {x_offset},{y_offset} Z" fill="none" stroke="black" stroke-width="1"/>'
        
        return pathoffset += height + 20  # Add space between sheets
        else:
            # Fall back to sample if no sheets detected
            entities.extend(self._generate_sample_box())
        
        # Assemble the full DXF
        full_dxf = dxf_header + ''.join(entities) + dxf_footer
        return full_dxf
    
    def _generate_sheet_with_joints(self, width, height, y_offset=0):
        entities = []
        x_offset = 10
        
        # Calculate number of fingers per edge
        fingers_per_edge = max(2, int((width / self.max_finger_width) / 2) * 2)
        finger_width = width / fingers_per_edge
        
        # Top edge with finger joints
        for i in range(fingers_per_edge):
            x_start = x_offset + i * finger_width
            x_end = x_offset + (i + 1) * finger_width
            
            if i % 2 == 0:  # Cut out
                entities.append(f"""0
LINE
8
0
10
{x_start}
20
{y_offset}
30
0
11
{x_start}
21
{y_offset + self.thickness}
31
0
""")
                if i > 0:
                    entities.append(f"""0
LINE
8
0
10
{x_start}
20
{y_offset + self.thickness}
30
0
11
{x_start - finger_width}
21
{y_offset + self.thickness}
31
0
""")
            else:  # Finger
                if i > 0:
                    entities.append(f"""0
LINE
8
0
10
{x_start}
20
{y_offset}
30
0
11
{x_start - finger_width}
21
{y_offset}
31
0
""")
        
        # Right side
        entities.append(f"""0
LINE
8
0
10
{x_offset + width}
20
{y_offset}
30
0
11
{x_offset + width}
21
{y_offset + height}
31
0
""")
        
        # Bottom edge
        entities.append(f"""0
LINE
8
0
10
{x_offset + width}
20
{y_offset + height}
30
0
11
{x_offset}
21
{y_offset + height}
31
0
""")
        
        # Left side
        entities.append(f"""0
LINE
8
0
10
{x_offset}
20
{y_offset + height}
30
0
11
{x_offset}
21
{y_offset}
31
0
""")
        
        return entities
    
    def _generate_sample_box(self):
        entities = []
        
        # Create a simple box with finger joints
        width, height = 80, 60
        
        # Bottom piece
        entities.extend(self._generate_sheet_with_joints(width, height, 0))
        
        # Side piece
        entities.extend(self._generate_sheet_with_joints(width, height, height + 20))
        
        # Another piece with different orientation
        entities.extend(self._generate_sheet_with_joints(height, width, 2 * height + 40))
        
        return entities
    
    def get_preview_svg(self):
        # Generate an SVG preview of our box with finger joints
        width, height = 80, 60
        thickness = self.thickness
        padding = 10
        
        # Calculate the viewbox size based on detected sheets or use defaults
        if self.sheets:
            max_width = max(sheet['width'] for sheet in self.sheets)
            total_height = sum(sheet['height'] for sheet in self.sheets) + (len(self.sheets) - 1) * 20
            viewbox_width = max_width + 2 * padding
            viewbox_height = total_height + 2 * padding
        else:
            viewbox_width = width + 2 * padding
            viewbox_height = (height * 3) + 4 * padding + 40
        
        svg_header = f'<svg viewBox="0 0 {viewbox_width} {viewbox_height}" xmlns="http://www.w3.org/2000/svg">'
        
        svg_content = []
        
        # If we have sheets from STL analysis, draw those
        if self.sheets:
            y_offset = padding
            for i, sheet in enumerate(self.sheets):
                # Create rectangles with finger joints for each sheet
                sheet_width = max(50, min(sheet['width'], 300))  # Limit size for display
                sheet_height = max(50, min(sheet['height'], 300))
                
                # Generate SVG path for this sheet
                svg_content.append(self._generate_sheet_svg_path(sheet_width, sheet_height, padding, y_offset))
                svg_content.append(f'<text x="{padding + sheet_width/2}" y="{y_offset + sheet_height + 15}" text-anchor="middle" font-size="6">Sheet {i+1}</text>')
                
                y_
