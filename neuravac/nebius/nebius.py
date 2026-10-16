from openai import OpenAI

from neuravac.secrets import get_secret


class Nebius_Interface:
    """OpenAI-compatible client configured for Nebius Token Factory."""

    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=get_secret("NEBIUS_API_KEY"),
            base_url="https://api.tokenfactory.nebius.com/v1",
        )


        self.model = "deepseek-ai/DeepSeek-V4-Flash-0731"

    def set_model(self, model: str) -> None:
        """Set the model to use for requests."""
        self.model = model

    def chat(self, messages: list[dict], **kwargs) -> dict:
        """Send a chat request to the Nebius API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return response

