// Global variables
let pyodide;
let dxfOutput = null;

// Initialize Pyodide when the page loads
async function main() {
    try {
        updateLoadStatus("Loading Pyodide...");
        pyodide = await loadPyodide();
        updateLoadStatus("Setting up Python environment...");
        
        // Import the Python script
        await pyodide.runPythonAsync(`
            import sys
            import io
            
            # Redirect stdout to capture logs
            class Logger:
                def __init__(self):
                    self.buffer = io.StringIO()
                
                def write(self, text):
                    self.buffer.write(text)
                    return len(text)
                
                def flush(self):
                    pass
                
                def get_logs(self):
                    return self.buffer.getvalue()
            
            sys.stdout = Logger()
        `);

        // Fetch and load our Python implementation
        updateLoadStatus("Loading Plycutter implementation...");
        const response = await fetch('simple_plycutter.py');
        const pythonCode = await response.text();
        await pyodide.runPythonAsync(pythonCode);
        
        // Enable the interface
        document.getElementById("processButton").disabled = false;
        document.getElementById("loading").style.display = "none";
        logMessage("Python environment loaded successfully");
        logMessage("Using simplified implementation for demo purposes");
        
    } catch (error) {
        updateLoadStatus(`Error: ${error.message}`);
        logMessage(`Failed to initialize Python environment: ${error.message}`);
        console.error("Pyodide initialization failed:", error);
    }
}

function updateLoadStatus(message) {
    document.getElementById("load-status").textContent = message;
    logMessage(message);
}

function logMessage(message) {
    const logElement = document.getElementById("log");
    logElement.innerHTML += message + "<br>";
    logElement.scrollTop = logElement.scrollHeight;
}

// Handle file upload and processing
document.addEventListener('DOMContentLoaded', function() {
    // Start loading Pyodide
    main();
    
    const stlFileInput = document.getElementById('stlFile');
    const processButton = document.getElementById('processButton');
    const downloadButton = document.getElementById('downloadButton');
    const plycutterForm = document.getElementById('plycutterForm');
    
    stlFileInput.addEventListener('change', function() {
        const fileName = this.files[0]?.name || '';
        logMessage(`Selected file: ${fileName}`);
    });
    
    plycutterForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!pyodide) {
            logMessage("Error: Python environment not loaded");
            return;
        }
        
        const stlFile = stlFileInput.files[0];
        if (!stlFile) {
            logMessage("Error: No STL file selected");
            return;
        }
        
        try {
            // Show loading indicator
            document.getElementById("loading").style.display = "flex";
            document.getElementById("load-status").textContent = "Processing STL file...";
            
            // Get form values
            const thickness = parseFloat(document.getElementById('thickness').value);
            const minFingerWidth = parseFloat(document.getElementById('minFingerWidth').value);
            const maxFingerWidth = parseFloat(document.getElementById('maxFingerWidth').value);
            const supportRadius = parseFloat(document.getElementById('supportRadius').value);
            const finalDilation = parseFloat(document.getElementById('finalDilation').value);
            const randomSeed = parseInt(document.getElementById('randomSeed').value);
            
            // Initialize Plycutter with the settings
            const initResult = await pyodide.runPythonAsync(`
                initialize_plycutter(
                    ${thickness},
                    ${minFingerWidth},
                    ${maxFingerWidth},
                    ${supportRadius},
                    ${finalDilation},
                    ${randomSeed}
                )
            `);
            logMessage(initResult);
            
            // Read the STL file
            const stlData = await stlFile.arrayBuffer();
            
            // Pass the STL data to Python
            const uint8Array = new Uint8Array(stlData);
            pyodide.FS.writeFile('input.stl', uint8Array);
            
            // Process the STL file
            logMessage("Processing STL file (this may take a moment)...");
            dxfOutput = await pyodide.runPythonAsync(`
                with open('input.stl', 'rb') as f:
                    stl_data = f.read()
                
                dxf_output = process_stl_file(stl_data)
                dxf_output
            `);
            
            // Get and display logs
            const logs = await pyodide.runPythonAsync('get_logs()');
            logs.split('\n').forEach(line => {
                if (line.trim()) logMessage(line.trim());
            });
            
            // Update the preview
            const svgPreview = await pyodide.runPythonAsync('get_svg_preview()');
            document.getElementById('preview-message').style.display = 'none';
            document.getElementById('preview-svg').innerHTML = svgPreview;
            
            // Enable the download button
            downloadButton.disabled = false;
            
            logMessage("Processing complete. You can now preview and download the DXF file.");
        } catch (error) {
            logMessage(`Error: ${error.message}`);
            console.error("Processing failed:", error);
        } finally {
            // Hide loading indicator
            document.getElementById("loading").style.display = "none";
        }
    });
    
    // Handle download button click
    downloadButton.addEventListener('click', function() {
        if (dxfOutput) {
            const blob = new Blob([dxfOutput], { type: 'application/dxf' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'plycutter_output.dxf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            logMessage("DXF file downloaded");
        } else {
            logMessage("No DXF output available for download");
        }
    });
});
