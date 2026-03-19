"""
Tests for the AI provider abstraction layer.

All tests use mocks — no real API calls are made.
Run with: pytest tests/test_ai_providers.py
"""
import sys
import os

# Ensure the backend directory is on the path so ai_providers can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ai_providers import execute, QuotaExhaustedError, ProviderError
from ai_providers.base import ProviderMessage, ProviderResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_messages(*contents: str) -> list[ProviderMessage]:
    return [ProviderMessage(role="user", content=c) for c in contents]


# ===========================================================================
# OpenAI Adapter Tests
# ===========================================================================

class TestOpenAIHappyPath:
    @pytest.mark.asyncio
    async def test_returns_provider_response(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hello!"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.model_dump.return_value = {"id": "chatcmpl-test"}

        with patch("ai_providers.openai_adapter.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            result = await execute(
                provider="openai",
                model="gpt-4",
                messages=make_messages("Hello"),
                api_key="sk-test",
            )

        assert isinstance(result, ProviderResponse)
        assert result.content == "Hello!"
        assert result.prompt_tokens == 10
        assert result.completion_tokens == 5
        assert result.total_tokens == 15
        assert result.raw_response == {"id": "chatcmpl-test"}

    @pytest.mark.asyncio
    async def test_messages_forwarded_correctly(self):
        """Verify that ProviderMessage objects are converted to dicts correctly."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "OK"
        mock_response.usage.prompt_tokens = 8
        mock_response.usage.completion_tokens = 2
        mock_response.usage.total_tokens = 10
        mock_response.model_dump.return_value = {}

        with patch("ai_providers.openai_adapter.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            create_mock = AsyncMock(return_value=mock_response)
            mock_client.chat.completions.create = create_mock

            await execute(
                provider="openai",
                model="gpt-4",
                messages=[
                    ProviderMessage(role="user", content="First"),
                    ProviderMessage(role="assistant", content="Second"),
                ],
                api_key="sk-test",
            )

        call_kwargs = create_mock.call_args
        messages_sent = call_kwargs.kwargs["messages"]
        assert messages_sent == [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
        ]


class TestOpenAISystemPrompt:
    @pytest.mark.asyncio
    async def test_system_prompt_injected_at_index_0(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hi"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 2
        mock_response.usage.total_tokens = 7
        mock_response.model_dump.return_value = {}

        with patch("ai_providers.openai_adapter.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            create_mock = AsyncMock(return_value=mock_response)
            mock_client.chat.completions.create = create_mock

            await execute(
                provider="openai",
                model="gpt-4",
                messages=[ProviderMessage(role="user", content="Hello")],
                api_key="sk-test",
                system_prompt="You are a helpful assistant.",
            )

        messages_sent = create_mock.call_args.kwargs["messages"]
        assert messages_sent[0] == {"role": "system", "content": "You are a helpful assistant."}
        assert messages_sent[1] == {"role": "user", "content": "Hello"}

    @pytest.mark.asyncio
    async def test_no_system_prompt_no_system_message(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hi"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 2
        mock_response.usage.total_tokens = 7
        mock_response.model_dump.return_value = {}

        with patch("ai_providers.openai_adapter.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            create_mock = AsyncMock(return_value=mock_response)
            mock_client.chat.completions.create = create_mock

            await execute(
                provider="openai",
                model="gpt-4",
                messages=[ProviderMessage(role="user", content="Hello")],
                api_key="sk-test",
                system_prompt=None,
            )

        messages_sent = create_mock.call_args.kwargs["messages"]
        assert all(m["role"] != "system" for m in messages_sent)


class TestOpenAIQuotaExhausted:
    @pytest.mark.asyncio
    async def test_rate_limit_error_raises_quota_exhausted(self):
        import openai as openai_lib

        with patch("ai_providers.openai_adapter.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                side_effect=openai_lib.RateLimitError(
                    message="Rate limit exceeded",
                    response=MagicMock(status_code=429, headers={}),
                    body={"error": {"code": "rate_limit_exceeded"}},
                )
            )

            with pytest.raises(QuotaExhaustedError):
                await execute(
                    provider="openai",
                    model="gpt-4",
                    messages=make_messages("Hello"),
                    api_key="sk-test",
                )

    @pytest.mark.asyncio
    async def test_insufficient_quota_code_raises_quota_exhausted(self):
        import openai as openai_lib
        import httpx

        mock_http_response = MagicMock(spec=httpx.Response)
        mock_http_response.status_code = 400
        mock_http_response.headers = {}
        mock_http_response.json.return_value = {
            "error": {"code": "insufficient_quota", "message": "Quota exceeded"}
        }

        with patch("ai_providers.openai_adapter.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                side_effect=openai_lib.BadRequestError(
                    message="Quota exceeded",
                    response=mock_http_response,
                    body={"error": {"code": "insufficient_quota", "message": "Quota exceeded"}},
                )
            )

            with pytest.raises(QuotaExhaustedError):
                await execute(
                    provider="openai",
                    model="gpt-4",
                    messages=make_messages("Hello"),
                    api_key="sk-test",
                )


class TestOpenAIProviderError:
    @pytest.mark.asyncio
    async def test_api_error_raises_provider_error(self):
        import openai as openai_lib
        import httpx

        mock_http_response = MagicMock(spec=httpx.Response)
        mock_http_response.status_code = 500
        mock_http_response.headers = {}
        mock_http_response.json.return_value = {"error": {"message": "Internal server error"}}

        with patch("ai_providers.openai_adapter.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                side_effect=openai_lib.InternalServerError(
                    message="Internal server error",
                    response=mock_http_response,
                    body={"error": {"message": "Internal server error"}},
                )
            )

            with pytest.raises(ProviderError):
                await execute(
                    provider="openai",
                    model="gpt-4",
                    messages=make_messages("Hello"),
                    api_key="sk-test",
                )


# ===========================================================================
# Claude Adapter Tests
# ===========================================================================

class TestClaudeHappyPath:
    @pytest.mark.asyncio
    async def test_returns_provider_response(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Claude says hello!")]
        mock_response.usage.input_tokens = 12
        mock_response.usage.output_tokens = 6
        mock_response.model_dump.return_value = {"id": "msg-test"}

        with patch("ai_providers.claude_adapter.AsyncAnthropic") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            result = await execute(
                provider="claude",
                model="claude-3-5-sonnet-20241022",
                messages=make_messages("Hello"),
                api_key="sk-ant-test",
            )

        assert isinstance(result, ProviderResponse)
        assert result.content == "Claude says hello!"
        assert result.prompt_tokens == 12
        assert result.completion_tokens == 6
        assert result.total_tokens == 18
        assert result.raw_response == {"id": "msg-test"}

    @pytest.mark.asyncio
    async def test_messages_forwarded_without_system_role(self):
        """System-role messages in the messages list should be excluded."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="OK")]
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 2
        mock_response.model_dump.return_value = {}

        with patch("ai_providers.claude_adapter.AsyncAnthropic") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            create_mock = AsyncMock(return_value=mock_response)
            mock_client.messages.create = create_mock

            await execute(
                provider="claude",
                model="claude-3-5-sonnet-20241022",
                messages=[
                    ProviderMessage(role="system", content="System instruction"),
                    ProviderMessage(role="user", content="User message"),
                ],
                api_key="sk-ant-test",
            )

        call_kwargs = create_mock.call_args.kwargs
        messages_sent = call_kwargs["messages"]
        # System-role message should be filtered out
        assert all(m["role"] != "system" for m in messages_sent)
        assert any(m["content"] == "User message" for m in messages_sent)


class TestClaudeSystemPrompt:
    @pytest.mark.asyncio
    async def test_system_prompt_passed_as_system_param(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.model_dump.return_value = {}

        with patch("ai_providers.claude_adapter.AsyncAnthropic") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            create_mock = AsyncMock(return_value=mock_response)
            mock_client.messages.create = create_mock

            await execute(
                provider="claude",
                model="claude-3-5-sonnet-20241022",
                messages=[ProviderMessage(role="user", content="Hello")],
                api_key="sk-ant-test",
                system_prompt="You are a pirate.",
            )

        call_kwargs = create_mock.call_args.kwargs
        assert call_kwargs.get("system") == "You are a pirate."

    @pytest.mark.asyncio
    async def test_no_system_prompt_omits_system_param(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.model_dump.return_value = {}

        with patch("ai_providers.claude_adapter.AsyncAnthropic") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            create_mock = AsyncMock(return_value=mock_response)
            mock_client.messages.create = create_mock

            await execute(
                provider="claude",
                model="claude-3-5-sonnet-20241022",
                messages=[ProviderMessage(role="user", content="Hello")],
                api_key="sk-ant-test",
                system_prompt=None,
            )

        call_kwargs = create_mock.call_args.kwargs
        assert "system" not in call_kwargs


class TestClaudeQuotaExhausted:
    @pytest.mark.asyncio
    async def test_rate_limit_error_raises_quota_exhausted(self):
        import anthropic as anthropic_lib

        with patch("ai_providers.claude_adapter.AsyncAnthropic") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                side_effect=anthropic_lib.RateLimitError(
                    message="Rate limit exceeded",
                    response=MagicMock(status_code=429, headers={}),
                    body={"error": {"type": "rate_limit_error"}},
                )
            )

            with pytest.raises(QuotaExhaustedError):
                await execute(
                    provider="claude",
                    model="claude-3-5-sonnet-20241022",
                    messages=make_messages("Hello"),
                    api_key="sk-ant-test",
                )

    @pytest.mark.asyncio
    async def test_overloaded_error_raises_quota_exhausted(self):
        import anthropic as anthropic_lib

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 529
        mock_http_resp.headers = {}

        with patch("ai_providers.claude_adapter.AsyncAnthropic") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                side_effect=anthropic_lib.APIStatusError(
                    message="Overloaded",
                    response=mock_http_resp,
                    body={"error": {"type": "overloaded_error"}},
                )
            )

            with pytest.raises(QuotaExhaustedError):
                await execute(
                    provider="claude",
                    model="claude-3-5-sonnet-20241022",
                    messages=make_messages("Hello"),
                    api_key="sk-ant-test",
                )

    @pytest.mark.asyncio
    async def test_resource_exhausted_message_raises_quota_exhausted(self):
        import anthropic as anthropic_lib

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 400
        mock_http_resp.headers = {}

        with patch("ai_providers.claude_adapter.AsyncAnthropic") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                side_effect=anthropic_lib.APIStatusError(
                    message="resource_exhausted: quota has been exceeded",
                    response=mock_http_resp,
                    body={},
                )
            )

            with pytest.raises(QuotaExhaustedError):
                await execute(
                    provider="claude",
                    model="claude-3-5-sonnet-20241022",
                    messages=make_messages("Hello"),
                    api_key="sk-ant-test",
                )


class TestClaudeProviderError:
    @pytest.mark.asyncio
    async def test_api_error_raises_provider_error(self):
        import anthropic as anthropic_lib

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 500
        mock_http_resp.headers = {}

        with patch("ai_providers.claude_adapter.AsyncAnthropic") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                side_effect=anthropic_lib.APIStatusError(
                    message="Internal server error",
                    response=mock_http_resp,
                    body={"error": {"type": "api_error"}},
                )
            )

            with pytest.raises(ProviderError):
                await execute(
                    provider="claude",
                    model="claude-3-5-sonnet-20241022",
                    messages=make_messages("Hello"),
                    api_key="sk-ant-test",
                )


# ===========================================================================
# Gemini Adapter Tests
# ===========================================================================

class TestGeminiHappyPath:
    @pytest.mark.asyncio
    async def test_returns_provider_response(self):
        mock_response = MagicMock()
        mock_response.text = "Gemini says hello!"
        mock_usage = MagicMock()
        mock_usage.prompt_token_count = 20
        mock_usage.candidates_token_count = 8
        mock_usage.total_token_count = 28
        mock_response.usage_metadata = mock_usage
        mock_response._pb = None  # Trigger fallback raw_response path

        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("ai_providers.gemini_adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock(return_value=MagicMock())

            result = await execute(
                provider="gemini",
                model="gemini-1.5-flash",
                messages=make_messages("Hello"),
                api_key="AIza-test",
            )

        assert isinstance(result, ProviderResponse)
        assert result.content == "Gemini says hello!"
        assert result.prompt_tokens == 20
        assert result.completion_tokens == 8
        assert result.total_tokens == 28

    @pytest.mark.asyncio
    async def test_zero_fallback_when_no_usage_metadata(self):
        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_response.usage_metadata = None

        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("ai_providers.gemini_adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock(return_value=MagicMock())

            result = await execute(
                provider="gemini",
                model="gemini-1.5-flash",
                messages=make_messages("Hello"),
                api_key="AIza-test",
            )

        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.total_tokens == 0


class TestGeminiSystemPrompt:
    @pytest.mark.asyncio
    async def test_system_prompt_prepended_to_first_user_message(self):
        mock_response = MagicMock()
        mock_response.text = "OK"
        mock_response.usage_metadata = None

        mock_chat = MagicMock()
        send_mock = AsyncMock(return_value=mock_response)
        mock_chat.send_message_async = send_mock

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("ai_providers.gemini_adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock(return_value=MagicMock())

            await execute(
                provider="gemini",
                model="gemini-1.5-flash",
                messages=[ProviderMessage(role="user", content="User question")],
                api_key="AIza-test",
                system_prompt="You are an expert coder.",
            )

        # The last_content (sent as the message) should contain the system prompt
        sent_content = send_mock.call_args.args[0]
        assert "You are an expert coder." in sent_content
        assert "User question" in sent_content

    @pytest.mark.asyncio
    async def test_assistant_role_converted_to_model(self):
        """Verify assistant messages are converted to 'model' role for Gemini."""
        mock_response = MagicMock()
        mock_response.text = "OK"
        mock_response.usage_metadata = None

        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)

        mock_model = MagicMock()
        start_chat_mock = MagicMock(return_value=mock_chat)
        mock_model.start_chat = start_chat_mock

        with patch("ai_providers.gemini_adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock(return_value=MagicMock())

            await execute(
                provider="gemini",
                model="gemini-1.5-flash",
                messages=[
                    ProviderMessage(role="user", content="Hello"),
                    ProviderMessage(role="assistant", content="Hi there"),
                    ProviderMessage(role="user", content="Follow-up"),
                ],
                api_key="AIza-test",
            )

        history = start_chat_mock.call_args.kwargs.get("history", [])
        # History should have the first two messages; last message is sent separately
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "model"


class TestGeminiQuotaExhausted:
    @pytest.mark.asyncio
    async def test_resource_exhausted_raises_quota_exhausted(self):
        from google.api_core.exceptions import ResourceExhausted

        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(
            side_effect=ResourceExhausted("Quota exceeded")
        )

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("ai_providers.gemini_adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock(return_value=MagicMock())

            with pytest.raises(QuotaExhaustedError):
                await execute(
                    provider="gemini",
                    model="gemini-1.5-flash",
                    messages=make_messages("Hello"),
                    api_key="AIza-test",
                )

    @pytest.mark.asyncio
    async def test_google_api_error_with_429_raises_quota_exhausted(self):
        from google.api_core.exceptions import GoogleAPIError

        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(
            side_effect=GoogleAPIError("429 quota exceeded")
        )

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("ai_providers.gemini_adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock(return_value=MagicMock())

            with pytest.raises(QuotaExhaustedError):
                await execute(
                    provider="gemini",
                    model="gemini-1.5-flash",
                    messages=make_messages("Hello"),
                    api_key="AIza-test",
                )


class TestGeminiProviderError:
    @pytest.mark.asyncio
    async def test_google_api_error_raises_provider_error(self):
        from google.api_core.exceptions import GoogleAPIError

        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(
            side_effect=GoogleAPIError("Internal server error")
        )

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("ai_providers.gemini_adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock(return_value=MagicMock())

            with pytest.raises(ProviderError):
                await execute(
                    provider="gemini",
                    model="gemini-1.5-flash",
                    messages=make_messages("Hello"),
                    api_key="AIza-test",
                )

    @pytest.mark.asyncio
    async def test_unexpected_exception_raises_provider_error(self):
        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(
            side_effect=RuntimeError("Unexpected error")
        )

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("ai_providers.gemini_adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock(return_value=MagicMock())

            with pytest.raises(ProviderError):
                await execute(
                    provider="gemini",
                    model="gemini-1.5-flash",
                    messages=make_messages("Hello"),
                    api_key="AIza-test",
                )


# ===========================================================================
# Router Tests
# ===========================================================================

class TestRouter:
    @pytest.mark.asyncio
    async def test_unknown_provider_raises_provider_error(self):
        with pytest.raises(ProviderError) as exc_info:
            await execute(
                provider="unknown_provider",
                model="some-model",
                messages=make_messages("Hello"),
                api_key="test-key",
            )

        assert "Unknown provider: unknown_provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_routes_to_openai(self):
        """Verify router delegates to openai_adapter."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Routed!"
        mock_response.usage.prompt_tokens = 1
        mock_response.usage.completion_tokens = 1
        mock_response.usage.total_tokens = 2
        mock_response.model_dump.return_value = {}

        with patch("ai_providers.openai_adapter.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            result = await execute(
                provider="openai",
                model="gpt-4",
                messages=make_messages("Route me"),
                api_key="sk-test",
            )

        assert result.content == "Routed!"

    @pytest.mark.asyncio
    async def test_routes_to_claude(self):
        """Verify router delegates to claude_adapter."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Claude routed!")]
        mock_response.usage.input_tokens = 1
        mock_response.usage.output_tokens = 1
        mock_response.model_dump.return_value = {}

        with patch("ai_providers.claude_adapter.AsyncAnthropic") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            result = await execute(
                provider="claude",
                model="claude-3-5-sonnet-20241022",
                messages=make_messages("Route me"),
                api_key="sk-ant-test",
            )

        assert result.content == "Claude routed!"

    @pytest.mark.asyncio
    async def test_routes_to_gemini(self):
        """Verify router delegates to gemini_adapter."""
        mock_response = MagicMock()
        mock_response.text = "Gemini routed!"
        mock_response.usage_metadata = None

        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("ai_providers.gemini_adapter.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock(return_value=MagicMock())

            result = await execute(
                provider="gemini",
                model="gemini-1.5-flash",
                messages=make_messages("Route me"),
                api_key="AIza-test",
            )

        assert result.content == "Gemini routed!"

    @pytest.mark.asyncio
    async def test_empty_provider_string_raises_provider_error(self):
        with pytest.raises(ProviderError) as exc_info:
            await execute(
                provider="",
                model="gpt-4",
                messages=make_messages("Hello"),
                api_key="sk-test",
            )

        assert "Unknown provider: " in str(exc_info.value)
