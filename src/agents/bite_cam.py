import base64
import io
import os

from openai import AsyncOpenAI

try:
    import PIL.Image as Image
except ImportError:
    from PIL import Image


class BiteCam:
    """BiteCam agent for extracting food items from images using GPT-4 vision"""

    def __init__(self):
        self.name = "bite_cam"

    async def run(self, image_b64: str):
        """
        Extract food items from base64 encoded image.

        Args:
            image_b64: Base64 encoded image data

        Returns:
            dict: {"raw_lines": list of extracted food item descriptions}
        """
        img = Image.open(io.BytesIO(base64.b64decode(image_b64)))
        img.thumbnail((1080, 1080))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        client = AsyncOpenAI()
        rsp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
                            },
                        },
                        {
                            "type": "text",
                            "text": "List each visible food item and its weight/volume if readable.",
                        },
                    ],
                }
            ],
        )
        return {"raw_lines": rsp.choices[0].message.content.splitlines()}
