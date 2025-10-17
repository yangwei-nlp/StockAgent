import ast
import re
from abc import ABC
from typing import Dict, List


class ChatResponse(ABC):
    """
    Represents a response from a chat model.

    This class encapsulates the content of a response from a chat model
    along with information about token usage.

    Attributes:
        content: The text content of the response.
        total_tokens: The total number of tokens used in the request and response.
    """

    def __init__(self, content: str, total_tokens: int) -> None:
        """
        Initialize a ChatResponse object.

        Args:
            content: The text content of the response.
            total_tokens: The total number of tokens used in the request and response.
        """
        self.content = content
        self.total_tokens = total_tokens

    def __repr__(self) -> str:
        """
        Return a string representation of the ChatResponse.

        Returns:
            A string representation of the ChatResponse object.
        """
        return f"ChatResponse(content={self.content}, total_tokens={self.total_tokens})"


class BaseLLM(ABC):
    """
    Abstract base class for language model implementations.

    This class defines the interface for language model implementations,
    including methods for chat-based interactions and parsing responses.
    """

    def __init__(self):
        """
        Initialize a BaseLLM object.
        """
        pass

    def chat(self, messages: List[Dict]) -> ChatResponse:
        """
        Send a chat message to the language model and get a response.

        Args:
            messages: A list of message dictionaries, typically in the format
                     [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        Returns:
            A ChatResponse object containing the model's response.
        """
        pass

    @staticmethod
    def literal_eval(response_content: str):
        """
        Parse a string response into a Python object using ast.literal_eval.

        This method attempts to extract and parse JSON or Python literals from the response content,
        handling various formats like code blocks and special tags.

        Args:
            response_content: The string content to parse.

        Returns:
            The parsed Python object.

        Raises:
            ValueError: If the response content cannot be parsed.
        """
        response_content = response_content.strip()

        response_content = BaseLLM.remove_think(response_content)

        try:
            if response_content.startswith("```") and response_content.endswith("```"):
                if response_content.startswith("```python"):
                    response_content = response_content[9:-3]
                elif response_content.startswith("```json"):
                    response_content = response_content[7:-3]
                elif response_content.startswith("```str"):
                    response_content = response_content[6:-3]
                elif response_content.startswith("```\n"):
                    response_content = response_content[4:-3]
                else:
                    raise ValueError("Invalid code block format")
            result = ast.literal_eval(response_content.strip())
        except Exception:
            matches = re.findall(r"(\[.*?\]|\{.*?\})", response_content, re.DOTALL)

            if len(matches) != 1:
                raise ValueError(
                    f"Invalid JSON/List format for response content:\n{response_content}"
                )

            json_part = matches[0]
            return ast.literal_eval(json_part)

        return result

    @staticmethod
    def remove_think(response_content: str) -> str:
        # remove content between <think> and </think>, especial for reasoning model
        if "<think>" in response_content and "</think>" in response_content:
            end_of_think = response_content.find("</think>") + len("</think>")
            response_content = response_content[end_of_think:]
        return response_content.strip()
