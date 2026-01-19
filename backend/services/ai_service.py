"""AI interpretation service using Claude API."""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any

import anthropic


class AIService:
    """Service for AI-powered MRI interpretation using Claude."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI service."""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        # Cache interpretations by series_id
        self.interpretation_cache: Dict[str, Dict[str, Any]] = {}

    def is_available(self) -> bool:
        """Check if the AI service is available."""
        return self.client is not None

    def get_cached_interpretation(self, series_id: str) -> Optional[Dict[str, Any]]:
        """Get cached interpretation for a series."""
        return self.interpretation_cache.get(series_id)

    def cache_interpretation(self, series_id: str, interpretation: Dict[str, Any]) -> None:
        """Cache interpretation for a series."""
        self.interpretation_cache[series_id] = interpretation

    async def interpret_images(
        self,
        images: List[Dict[str, str]],
        context: Optional[str] = None,
        modality: str = "MRI",
        series_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze MRI images and provide interpretation."""
        # Check cache first
        if series_id and series_id in self.interpretation_cache:
            cached = self.interpretation_cache[series_id]
            cached["from_cache"] = True
            return cached

        if not self.is_available():
            return {
                "success": False,
                "error": "AI service not configured. Please set ANTHROPIC_API_KEY environment variable."
            }

        if not images:
            return {
                "success": False,
                "error": "No images provided for interpretation."
            }

        system_prompt = """You are a medical imaging AI assistant. Provide CONCISE interpretations.

IMPORTANT: This is for educational/research purposes only, NOT clinical use.

Response format (be brief, use bullet points):

**CRITICAL FINDINGS** (if any)
- List urgent/abnormal findings first
- Be specific: location, size, characteristics

**NORMAL STRUCTURES**
- List organs/structures that appear normal
- Keep each item to one line

**IMAGE QUALITY**
- Brief note on quality/limitations

Keep total response under 300 words. Be direct and clinical."""

        user_content = []

        if context:
            user_content.append({
                "type": "text",
                "text": f"Clinical context: {context}"
            })

        user_content.append({
            "type": "text",
            "text": f"Analyze this {modality} image. List critical findings first, then normal structures."
        })

        for img in images:
            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img.get("media_type", "image/png"),
                    "data": img["data"]
                }
            })

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
            )

            response_text = ""
            for block in message.content:
                if hasattr(block, "text"):
                    response_text += block.text

            result = {
                "success": True,
                "interpretation": response_text,
                "model": message.model,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                },
                "disclaimer": "Educational/research use only. Not for clinical decisions.",
                "from_cache": False,
                "generated_at": datetime.now().isoformat()
            }

            # Cache the result
            if series_id:
                self.cache_interpretation(series_id, result)

            return result

        except anthropic.APIError as e:
            return {
                "success": False,
                "error": f"API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def clear_cache(self, series_id: str) -> None:
        """Clear cached interpretation for a series."""
        if series_id in self.interpretation_cache:
            del self.interpretation_cache[series_id]

    async def interpret_series(
        self,
        slice_images: List[str],
        sample_count: int = 5,
        context: Optional[str] = None,
        modality: str = "MRI",
        series_id: Optional[str] = None,
        refresh: bool = False
    ) -> Dict[str, Any]:
        """Analyze a series of MRI slices by sampling representative images."""
        # Clear cache if refresh requested
        if refresh and series_id:
            self.clear_cache(series_id)

        # Check cache first (if not refreshing)
        if not refresh and series_id and series_id in self.interpretation_cache:
            cached = self.interpretation_cache[series_id].copy()
            cached["from_cache"] = True
            return cached

        if not slice_images:
            return {
                "success": False,
                "error": "No images provided for interpretation."
            }

        total_slices = len(slice_images)
        if total_slices <= sample_count:
            sampled_images = slice_images
        else:
            indices = [int(i * (total_slices - 1) / (sample_count - 1)) for i in range(sample_count)]
            sampled_images = [slice_images[i] for i in indices]

        images = [
            {"data": img, "media_type": "image/png"}
            for img in sampled_images
        ]

        return await self.interpret_images(images, context, modality, series_id)


# Global instance
ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get the global AI service instance."""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service
