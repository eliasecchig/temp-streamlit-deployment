# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field


class InputChat(BaseModel):
    """Represents the input for a chat session."""

    messages: List[
        Annotated[
            Union[HumanMessage, AIMessage, ToolMessage], Field(discriminator="type")
        ]
    ] = Field(
        ..., description="The chat messages representing the current conversation."
    )
    user_id: str = ""
    session_id: str = ""


class Input(BaseModel):
    """Wrapper class for InputChat."""

    input: InputChat


class Feedback(BaseModel):
    """Represents feedback for a conversation."""

    score: Union[int, float]
    text: Optional[str] = ""
    run_id: str
    log_type: Literal["feedback"] = "feedback"


def default_serialization(obj: Any) -> Any:
    """
    Default serialization for LangChain objects.
    Converts BaseModel instances to dictionaries.
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump()


def extract_human_ai_messages(
    messages: List[Union[Dict[str, Any], BaseModel]]
) -> List[Dict[str, Any]]:
    """
    Extract AI and human messages with non-empty content from a list of messages.
    The function will remove all messages relative to tool calls (Empty AI Messages
    with tool calls and ToolMessages).

    Args:
        messages (List[Union[Dict[str, Any], BaseModel]]): A list of message objects.

    Returns:
        List[Dict[str, Any]]: A list of extracted AI and human messages with
        non-empty content.
    """
    extracted_messages = []
    for message in messages:
        if isinstance(message, BaseModel):
            message = message.model_dump()

        is_valid_type = message.get("type") in ["human", "ai"]
        has_content = bool(message.get("content"))

        if is_valid_type and has_content:
            extracted_messages.append(message)

    return extracted_messages


def extract_tool_calls_and_messages(
    messages: List[Union[Dict[str, Any], BaseModel]]
) -> List[Dict[str, Any]]:
    """
    Extract AI Messages with tool calls and ToolMessages from a list of messages.
    AI Messages with tool calls define tool inputs, while ToolMessages contain outputs.

    Args:
        messages (List[Union[Dict[str, Any], BaseModel]]): A list of message objects.

    Returns:
        List[Dict[str, Any]]: A list of extracted tool calls and .
    """
    extracted_messages = []
    for message in messages:
        if isinstance(message, BaseModel):
            message = message.model_dump()

        is_tool_message = message.get("type") == "tool"
        is_ai_with_tool_call = message.get("type") == "ai" and message.get("tool_calls")

        if is_tool_message or is_ai_with_tool_call:
            extracted_messages.append(message)

    return extracted_messages
