from fastapi import APIRouter, Form
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


# -----------------------------
# Pydantic schema for JSON API
# -----------------------------
class PromptRequest(BaseModel):
    story_prompt: str
    character_name: str
    setting: str
    tone: str
    art_style: str


# -----------------------------
# AI function placeholders
# Replace these with your actual
# Gemini functions later
# -----------------------------

def generate_outline(story_prompt, character_name, setting, tone, art_style):
    return {
        "panels": [
            {
                "panel": 1,
                "description": story_prompt
            }
        ]
    }


def generate_story(outline, character_name, tone):
    return {
        "panels": [
            {
                "panel": 1,
                "narration": outline["panels"][0]["description"],
                "dialogue": f"{character_name}: Let's begin our adventure!"
            }
        ]
    }


def generate_image(prompt, art_style):
    return {
        "image_prompt": prompt,
        "art_style": art_style,
        "image": None
    }


def build_comic_layout(story, images):
    return {
        "story": story,
        "images": images
    }


def save_pdf(layout):
    return "output/comic.pdf"


# -----------------------------
# HTML Form route
# /generate
# -----------------------------

@router.post("/generate")
async def generate_comic(
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...)
):

    outline = generate_outline(
        story_prompt,
        character_name,
        setting,
        tone,
        art_style
    )

    story = generate_story(
        outline,
        character_name,
        tone
    )

    images = []

    for panel in story["panels"]:
        image = generate_image(
            panel["narration"],
            art_style
        )
        images.append(image)

    layout = build_comic_layout(
        story,
        images
    )

    pdf_path = save_pdf(layout)

    return {
        "success": True,
        "layout": layout,
        "pdf_path": pdf_path
    }


# -----------------------------
# JSON API route
# /generate-comic/json
# -----------------------------

@router.post("/generate-comic/json")
async def generate_comic_json(request: PromptRequest):

    outline = generate_outline(
        request.story_prompt,
        request.character_name,
        request.setting,
        request.tone,
        request.art_style
    )

    story = generate_story(
        outline,
        request.character_name,
        request.tone
    )

    images = []

    for panel in story["panels"]:
        image = generate_image(
            panel["narration"],
            request.art_style
        )
        images.append(image)

    layout = build_comic_layout(
        story,
        images
    )

    pdf_path = save_pdf(layout)

    return {
        "success": True,
        "layout": layout,
        "pdf_path": pdf_path
    }


# -----------------------------
# Image testing route
# /test-image
# -----------------------------

@router.get("/test-image")
async def test_image(
    prompt: str = "A superhero standing in a futuristic city",
    art_style: str = "comic"
):

    image = generate_image(
        prompt,
        art_style
    )

    return {
        "success": True,
        "result": image
    }
