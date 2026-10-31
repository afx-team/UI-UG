from openai import OpenAI
import requests
import base64
import os
from typing import Optional, Dict, Any


class VLLMChatInference:
    """
    Optimized VLLM Chat Inference Implementation

    Features:
    1. Configurable API endpoints with multiple presets
    2. Support for both streaming and non-streaming modes
    3. Better error handling
    4. Configurable max_tokens
    5. Type hints
    """

    def __init__(self, api_key: Optional[str] = None, api_base: str = None, max_tokens: int = 8192):
        """
        Initialize VLLM chat inference with configurable endpoints.

        :param api_key: OpenAI API key (default: "EMPTY")
        :param api_base: API base URL.
               If None, defaults to env `VLLM_API_BASE`,
               then falls back to http://127.0.0.1:8000/v1
        :param max_tokens: Maximum tokens in response (default: 7000)
        """
        self.max_tokens = max_tokens
        self.api_base = api_base or os.getenv("VLLM_API_BASE", "http://127.0.0.1:8000/v1")
        self.client = OpenAI(api_key=api_key or os.getenv("VLLM_API_KEY", "EMPTY"), base_url=self.api_base)

    def image_to_base64(self, input_value: str) -> str:
        """
        Convert image to Base64 encoding.

        :param input_value: Image URL (http/https) or local file path
        :return: Base64 encoded string
        """
        if input_value.startswith(("http://", "https://")):
            # Fetch image from URL
            response = requests.get(input_value, timeout=30)
            response.raise_for_status()
            return base64.b64encode(response.content).decode('utf-8')
        else:
            # Read local file
            if not os.path.isfile(input_value):
                raise FileNotFoundError(f"Image file not found: {input_value}")
            with open(input_value, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')

    def image_to_data_url(self, input_value: str) -> str:
        from io import BytesIO
        from PIL import Image
        encoded = self.image_to_base64(input_value)
        with Image.open(BytesIO(base64.b64decode(encoded))) as image:
            mime = Image.MIME.get(image.format)
        if not mime:
            raise ValueError("Unsupported image MIME type")
        return f"data:{mime};base64,{encoded}"

    def build_messages(self, prompt: str, image_base64: Optional[str] = None) -> list:
        """Build messages for chat completion."""
        if image_base64 is not None:
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_base64 if image_base64.startswith("data:") else f"data:image/jpeg;base64,{image_base64}",
                            "min_pixels": 224 * 224,
                            "max_pixels": 1280 * 28 * 28
                        }
                    }
                ]
            }]
        else:
            messages = [{"role": "user", "content": prompt}]
        return messages

    def chat_with_image(self,
                        model_name: str,
                        prompt: str,
                        image_path_or_url: Optional[str] = None,
                        temperature: float = 0.1,
                        extra_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate response with image and text.

        :param model_name: Name of the model
        :param prompt: Text prompt
        :param image_path_or_url: Image URL or local path (None for text-only)
        :param temperature: Sampling temperature (0-1)
        :param extra_params: Additional parameters for completion
        :return: Model response text
        """
        extra_params = extra_params or {"chat_template_kwargs": {"enable_thinking": False}}

        # Process image if provided
        image_base64 = None
        if image_path_or_url is not None:
            image_base64 = self.image_to_data_url(image_path_or_url)

        messages = self.build_messages(prompt, image_base64)

        # Call API
        response = self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            extra_body=extra_params,
            max_tokens=self.max_tokens
        )

        result = response.choices[0].message.content
        return result

    def chat_with_image_stream(self,
                               model_name: str,
                               prompt: str,
                               image_path_or_url: Optional[str] = None,
                               temperature: float = 0.1,
                               extra_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate streaming response with image and text.

        :return: Accumulated response text
        """
        extra_params = extra_params or {"chat_template_kwargs": {"enable_thinking": False}}

        # Process image if provided
        image_base64 = None
        if image_path_or_url is not None:
            image_base64 = self.image_to_data_url(image_path_or_url)

        messages = self.build_messages(prompt, image_base64)

        # Streaming response
        stream = self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            stream=True,
            extra_body=extra_params,
            max_tokens=self.max_tokens
        )

        # Accumulate response
        response_text = ""
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content is not None:
                response_text += delta.content
            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                # Handle reasoning content if present
                pass

        return response_text
