import os
import json
import re
import subprocess  # NEW: Allows us to capture error logs
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRequest(BaseModel):
    description: str

SYSTEM_PROMPT = """
You are a Manim Animation Expert.
Output a JSON object with exactly two keys:
1. "scene_logic": A list of strings explaining the animation steps.
2. "manim_code": A complete, runnable Python script using Manim.
   - CLASS NAME: Must be 'class GenScene(Scene):'
   - IMPORTS: Start with 'from manim import *'
   - NO MARKDOWN: Return raw code only (no ```python).
"""

@app.post("/generate")
async def generate_animation(request: UserRequest):
    try:
        print(f"Processing: {request.description}")
        
        # 1. AI Generation
        model = genai.GenerativeModel('gemini-pro-latest', 
                                      system_instruction=SYSTEM_PROMPT,
                                      generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(request.description)
        
        data = json.loads(response.text)
        code = data["manim_code"]
        logic = data["scene_logic"]

        # Clean code
        code = re.sub(r"```python\n?", "", code)
        code = re.sub(r"```", "", code)

        with open("generated_scene.py", "w", encoding="utf-8") as f:
            f.write(code)

        # 2. Render with Debug Logging (The Fix)
        print("Rendering with Manim... (This may take 30 seconds)")
        
        # Run Manim and capture the output
        process = subprocess.run(
            ["manim", "-ql", "-o", "final_video.mp4", "generated_scene.py", "GenScene"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        # If it failed, print the REAL error
        if process.returncode != 0:
            print("\n" + "="*20 + " MANIM ERROR LOG " + "="*20)
            print(process.stderr)  # <--- THIS WILL SHOW WHY IT FAILED
            print("="*60 + "\n")
            raise Exception("Manim execution failed. See terminal for details.")

        video_path = "media/videos/generated_scene/480p15/final_video.mp4"
        if not os.path.exists(video_path):
             raise Exception("Video file missing.")

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
