"""
OpenAI API client wrapper for centralized API interaction.
"""

import os
import time
from collections.abc import Iterator
from typing import Any, Optional

from openai import APIConnectionError, APIError, OpenAI, RateLimitError


class OpenAIClient:
    """Client wrapper for OpenAI API interactions."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY env var.

        Raises:
            ValueError: If no API key is provided.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = OpenAI(api_key=self.api_key)

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_completion_tokens: Optional[int] = None,
        max_retries: int = 0,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create a chat completion.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            model: Model to use for completion.
            temperature: Sampling temperature (0-2).
            max_completion_tokens: Maximum tokens in response.
            max_retries: Number of retries for transient failures.
            **kwargs: Additional parameters for the API.

        Returns:
            Dictionary with 'content' and 'usage' information.
        """
        retries = 0
        last_error = None

        while retries <= max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_completion_tokens,
                    **kwargs,
                )

                return {
                    "content": response.choices[0].message.content,
                    "usage": (
                        {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                        }
                        if hasattr(response, "usage")
                        else None
                    ),
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason,
                }

            except APIConnectionError as e:
                last_error = e
                retries += 1
                if retries <= max_retries:
                    time.sleep(1 * retries)  # Exponential backoff
                    continue
                raise

            except (APIError, RateLimitError):
                # Don't retry on API errors or rate limits
                raise

        # If we've exhausted retries, raise the last error
        if last_error:
            raise last_error

    def analyze_image(
        self,
        image_url: str,
        prompt: str,
        model: str = "gpt-4-vision-preview",
        max_completion_tokens: int = 300,
    ) -> dict[str, Any]:
        """
        Analyze an image using GPT-4 Vision.

        Args:
            image_url: URL of the image to analyze.
            prompt: Question or prompt about the image.
            model: Vision model to use.
            max_completion_tokens: Maximum tokens in response.

        Returns:
            Dictionary with analysis results.
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]

        response = self.client.chat.completions.create(
            model=model, messages=messages, max_completion_tokens=max_completion_tokens
        )

        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "finish_reason": response.choices[0].finish_reason,
        }

    def generate_recipe_suggestions(
        self,
        ingredients: list[str],
        dietary_restrictions: Optional[list[str]] = None,
        cuisine_preference: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
    ) -> dict[str, Any]:
        """
        Generate recipe suggestions based on ingredients and preferences.

        Args:
            ingredients: List of available ingredients.
            dietary_restrictions: List of dietary restrictions.
            cuisine_preference: Preferred cuisine type.
            model: Model to use for generation.

        Returns:
            Dictionary with recipe suggestions.
        """
        system_message = (
            "You are a helpful cooking assistant that suggests recipes based on "
            "available ingredients and dietary preferences. Provide practical and "
            "delicious recipe suggestions."
        )

        user_message_parts = [f"I have these ingredients: {', '.join(ingredients)}."]

        if dietary_restrictions:
            user_message_parts.append(f"Dietary restrictions: {', '.join(dietary_restrictions)}.")

        if cuisine_preference:
            user_message_parts.append(f"I prefer {cuisine_preference} cuisine.")

        user_message_parts.append("Please suggest 3-5 recipes I can make with these ingredients.")

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": " ".join(user_message_parts)},
        ]

        result = self.chat_completion(messages=messages, model=model)

        return {
            "suggestions": result["content"],
            "model": result["model"],
            "usage": result.get("usage"),
        }

    def moderate_content(self, text: str) -> dict[str, Any]:
        """
        Check if content violates OpenAI usage policies.

        Args:
            text: Text to moderate.

        Returns:
            Dictionary with moderation results.
        """
        response = self.client.moderations.create(input=text)

        result = response.results[0]

        return {
            "flagged": result.flagged,
            "categories": {
                "hate": result.categories.hate,
                "violence": result.categories.violence,
                "self_harm": result.categories.self_harm,
                "sexual": result.categories.sexual,
            },
            "scores": {
                "hate": result.category_scores.hate,
                "violence": result.category_scores.violence,
                "self_harm": result.category_scores.self_harm,
                "sexual": result.category_scores.sexual,
            },
        }

    def create_embedding(self, text: str, model: str = "text-embedding-ada-002") -> dict[str, Any]:
        """
        Create an embedding for the given text.

        Args:
            text: Text to embed.
            model: Embedding model to use.

        Returns:
            Dictionary with embedding and metadata.
        """
        response = self.client.embeddings.create(model=model, input=text)

        return {
            "embedding": response.data[0].embedding,
            "model": response.model,
            "tokens_used": response.usage.total_tokens,
        }

    def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        **kwargs,
    ) -> Iterator[str]:
        """
        Stream a chat completion response.

        Args:
            messages: List of message dictionaries.
            model: Model to use.
            temperature: Sampling temperature.
            **kwargs: Additional parameters.

        Yields:
            Chunks of the response content.
        """
        stream = self.client.chat.completions.create(
            model=model, messages=messages, temperature=temperature, stream=True, **kwargs
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # OpenAI client doesn't need explicit cleanup
        pass
