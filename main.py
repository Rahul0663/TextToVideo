import os
import json
import re
import sys
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# 2. Enable Frontend Connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRequest(BaseModel):
    description: str
# REPLACE SYSTEM_PROMPT IN main.py WITH THIS
SYSTEM_PROMPT = """
You are a Manim Animation Expert (v0.19.0).
Output JSON with keys: "scene_logic" and "manim_code".

### CRITICAL RULES
1. **CLASS NAME:** Must be 'class GenScene(ThreeDScene):' for 3D.
2. **NO .lines ATTRIBUTE:** Polygons DO NOT have .lines. Use get_vertices().
3. **NO 'vertex_config':** Polyhedron() does NOT accept 'vertex_config'.
4. **NO 'fill_color' in Polyhedron:** Polyhedron() does NOT accept fill_color directly.
   - USE: faces_config={"fill_color": RED, "fill_opacity": 0.5}
   - OR: poly.set_fill(color=RED, opacity=0.5)
5. **NO 'Pyramid' CLASS:** Use 'Cone' or construct a Polyhedron manually.
6. **RAW STRINGS:** Use r"..." for MathTex.

### CORRECT CODE PATTERNS
- **Manual Pyramid (Polyhedron):**
  # GOOD:
  vertices = [[1, 1, 0], [1, -1, 0], [-1, -1, 0], [-1, 1, 0], [0, 0, 2]]
  faces = [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4], [0, 1, 2, 3]]
  
  # Note: Use faces_config for color, NOT fill_color
  pyramid = Polyhedron(
      vertex_coords=vertices, 
      faces_list=faces, 
      faces_config={"fill_color": BLUE, "fill_opacity": 0.5}
  )

- **To show a right angle:**
  # GOOD: right_angle = RightAngle(line1, line2, length=0.4)
"""
def clean_json_response(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
    raise ValueError("Failed to extract valid JSON from AI response")

@app.post("/generate")
async def generate_animation(request: UserRequest):
    try:
        print(f"Processing: {request.description}")
        
        # A. Call AI
        model = genai.GenerativeModel('gemini-pro-latest', 
                                      system_instruction=SYSTEM_PROMPT,
                                      generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(request.description)
        
        # B. Parse
        try:
            data = clean_json_response(response.text)
        except Exception as e:
            print(f"Raw AI Output: {response.text}")
            raise Exception("AI returned invalid JSON. Please try again.")

        code = data["manim_code"]
        logic = data["scene_logic"]

        # Clean markdown
        code = re.sub(r"```python\n?", "", code)
        code = re.sub(r"```", "", code)

        # === SAFETY FIX: Force Imports ===
        if "from manim import *" not in code:
            code = "from manim import *\n" + code
        if "import numpy" not in code:
            code = "import numpy as np\n" + code
        # =================================

        # C. Save Code
        with open("generated_scene.py", "w", encoding="utf-8") as f:
            f.write(code)

        # D. Render
        print("Rendering with Manim...")
        process = subprocess.run(
            [sys.executable, "-m", "manim", "-ql", "-o", "final_video.mp4", "generated_scene.py", "GenScene"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if process.returncode != 0:
            print("\n" + "="*20 + " MANIM ERROR LOG " + "="*20)
            print(process.stderr)
            print(process.stdout)
            print("="*60 + "\n")
            raise Exception("Manim execution failed. See terminal for log.")

        # E. Verify Output
        video_path = "media/videos/generated_scene/480p15/final_video.mp4"
        if not os.path.exists(video_path):
             raise Exception("Video file not found.")

        return {
            "videoUrl": "http://localhost:8000/video",
            "sceneLogic": logic,
            "generatedCode": code
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video")
def get_video():
    video_path = "media/videos/generated_scene/480p15/final_video.mp4"
    if os.path.exists(video_path):
        return FileResponse(video_path)
    return {"error": "Video not found"}
