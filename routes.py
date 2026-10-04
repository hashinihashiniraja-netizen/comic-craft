import os
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")


class PromptRequest(BaseModel):
    story_prompt: str
    character_name: str
    setting: str
    tone: str
    art_style: str


def generate_with_gemini(prompt: str) -> str:
    """Generate text with Gemini when an API key is available."""
    if not GEMINI_API_KEY:
        return (
            "Gemini API key is not configured yet. "
            "The comic structure was created successfully."
        )

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return response.text or "No response generated."

    except Exception as exc:
        return f"Gemini generation unavailable: {exc}"


def generate_outline(data: PromptRequest) -> dict:
    prompt = f"""
Create a short comic story outline.

Story idea: {data.story_prompt}
Main character: {data.character_name}
Setting: {data.setting}
Tone: {data.tone}
Art style: {data.art_style}

Create 4 comic panels.
For every panel provide:
1. scene description
2. narration
3. dialogue
4. image prompt
"""

    ai_text = generate_with_gemini(prompt)

    return {
        "title": "AI Comic Story",
        "character": data.character_name,
        "setting": data.setting,
        "tone": data.tone,
        "art_style": data.art_style,
        "outline": ai_text,
    }


def generate_story(outline: dict) -> dict:
    return {
        "title": outline["title"],
        "character": outline["character"],
        "setting": outline["setting"],
        "tone": outline["tone"],
        "art_style": outline["art_style"],
        "story": outline["outline"],
    }


def generate_image(prompt: str, art_style: str) -> dict:
    """
    Optional Hugging Face image generation.
    If HF token is unavailable, the route still works and returns
    an image prompt for later generation.
    """
    image_path = None

    if HF_API_KEY:
        try:
            from huggingface_hub import InferenceClient

            client = InferenceClient(
                provider="hf-inference",
                api_key=HF_API_KEY,
            )

            image = client.text_to_image(
                f"{prompt}, {art_style}, comic book panel"
            )

            image_path = OUTPUT_DIR / "comic_panel.png"
            image.save(image_path)

        except Exception:
            image_path = None

    return {
        "image_prompt": prompt,
        "art_style": art_style,
        "image": str(image_path) if image_path else None,
    }


def build_comic_layout(story: dict) -> dict:
    return {
        "title": story["title"],
        "character": story["character"],
        "setting": story["setting"],
        "tone": story["tone"],
        "art_style": story["art_style"],
        "story": story["story"],
    }


def save_pdf(comic: dict) -> str:
    pdf_path = OUTPUT_DIR / "comic.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, comic["title"], ln=True)

    pdf.ln(5)

    pdf.set_font("Helvetica", "", 12)

    details = (
        f"Character: {comic['character']}\n"
        f"Setting: {comic['setting']}\n"
        f"Tone: {comic['tone']}\n"
        f"Art Style: {comic['art_style']}\n"
    )

    pdf.multi_cell(0, 8, details)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Comic Story", ln=True)

    pdf.set_font("Helvetica", "", 11)

    story_text = str(comic["story"])

    # Keep PDF safe for standard Helvetica encoding.
    story_text = story_text.encode(
        "latin-1", "replace"
    ).decode("latin-1")

    pdf.multi_cell(0, 7, story_text)

    pdf.output(str(pdf_path))

    return str(pdf_path)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    data = PromptRequest(
        story_prompt=story_prompt,
        character_name=character_name,
        setting=setting,
        tone=tone,
        art_style=art_style,
    )

    outline = generate_outline(data)
    story = generate_story(outline)
    comic = build_comic_layout(story)

    pdf_path = save_pdf(comic)

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "comic": comic,
            "pdf_path": pdf_path,
        },
    )


@router.post("/generate-comic/json")
async def generate_comic_json(data: PromptRequest):
    outline = generate_outline(data)
    story = generate_story(outline)
    comic = build_comic_layout(story)
    pdf_path = save_pdf(comic)

    return {
        "success": True,
        "comic": comic,
        "pdf": pdf_path,
    }


@router.get("/download-pdf")
async def download_pdf():
    pdf_path = OUTPUT_DIR / "comic.pdf"

    if not pdf_path.exists():
        return {
            "error": "PDF has not been generated yet."
        }

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename="comic.pdf",
    )


@router.get("/test-image")
async def test_image():
    result = generate_image(
        "A friendly superhero standing in a colorful city",
        "comic book",
    )

    return {
        "success": True,
        "result": result,
    }


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "gemini_configured": bool(GEMINI_API_KEY),
        "huggingface_configured": bool(HF_API_KEY),
    }