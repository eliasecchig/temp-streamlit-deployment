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

import uuid
from functools import wraps
from types import GeneratorType
from typing import Any, AsyncGenerator, Callable, Dict, List, Literal

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from pydantic import BaseModel, Field
from traceloop.sdk import TracerWrapper
from traceloop.sdk.decorators import workflow


class BaseCustomChainEvent(BaseModel):
    name: str = "custom_chain_event"

    class Config:
        extra = "allow"


class OnToolStartEvent(BaseCustomChainEvent):
    event: Literal["on_tool_start"] = "on_tool_start"
    input: Dict = {}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ToolData(BaseModel):
    input: Dict = {}
    output: ToolMessage


class OnToolEndEvent(BaseCustomChainEvent):
    event: Literal["on_tool_end"] = "on_tool_end"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data: ToolData


class ChatModelStreamData(BaseModel):
    chunk: AIMessageChunk


class OnChatModelStreamEvent(BaseCustomChainEvent):
    event: Literal["on_chat_model_stream"] = "on_chat_model_stream"
    data: ChatModelStreamData


class Event(BaseModel):
    event: str = "data"
    data: dict


class EndEvent(BaseModel):
    event: Literal["end"] = "end"


def create_on_tool_end_event_from_retrieval(
    query: str,
    docs: List[Document],
    tool_call_id: str = "retriever",
    name: str = "retriever",
) -> OnToolEndEvent:
    """
    Create a LangChain Astream events v2 compatible on_tool_end_event from a retrieval process.

    Args:
        query (str): The query used for retrieval.
        docs (List[Document]): The retrieved documents.
        tool_call_id (str, optional): The ID of the tool call. Defaults to "retriever".
        name (str, optional): The name of the tool. Defaults to "retriever".

    Returns:
        OnToolEndEvent: An event representing the end of the retrieval tool execution.
    """
    ranked_docs_tool_output = ToolMessage(
        tool_call_id=tool_call_id, content=[doc.model_dump() for doc in docs], name=name
    )
    return OnToolEndEvent(
        data=ToolData(input={"query": query}, output=ranked_docs_tool_output)
    )


class CustomChain:
    """A custom chain class that wraps a callable function."""

    def __init__(self, func: Callable):
        """Initialize the CustomChain with a callable function."""
        self.func = func

    async def astream_events(self, *args: Any, **kwargs: Any) -> AsyncGenerator:
        """
        Asynchronously stream events from the wrapped function.
        Applies Traceloop workflow decorator if Traceloop SDK is initialized.
        """

        if hasattr(TracerWrapper, "instance"):
            func = workflow()(self.func)
        else:
            func = self.func

        gen: GeneratorType = func(*args, **kwargs)
        for event in gen:
            yield event.model_dump()

    def invoke(self, *args: Any, **kwargs: Any) -> AIMessage:
        """
        Invoke the wrapped function and process its events.
        Returns an AIMessage with content and relative tool calls.
        """
        events = self.func(*args, **kwargs)
        response_content = ""
        tool_calls = []
        for event in events:
            if isinstance(event, OnChatModelStreamEvent):
                if not isinstance(event.data.chunk.content, str):
                    raise ValueError("Chunk content must be a string")
                response_content += event.data.chunk.content
            elif isinstance(event, OnToolEndEvent):
                tool_calls.append(event.data.model_dump())
        return AIMessage(
            content=response_content, additional_kwargs={"tool_calls_data": tool_calls}
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Make the CustomChain instance callable, invoking the wrapped function."""
        return self.func(*args, **kwargs)


def custom_chain(func: Callable) -> CustomChain:
    """
    Decorator function that wraps a callable in a CustomChain instance.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return CustomChain(wrapper)
