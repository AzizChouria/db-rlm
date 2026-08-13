"""Core RLM implementation."""

import asyncio
import re
from typing import Optional, Dict, Any, List

import litellm

from .types import Message
from .repl import REPLExecutor, REPLError
from .prompts import build_system_prompt
from .parser import parse_response, is_final


class RLMError(Exception):
    """Base error for RLM."""
    pass


class MaxIterationsError(RLMError):
    """Max iterations exceeded."""
    pass


class MaxDepthError(RLMError):
    """Max recursion depth exceeded."""
    pass


class RLM:
    """Recursive Language Model."""

    def __init__(
        self,
        model: str,
        recursive_model: Optional[str] = None,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        max_depth: int = 5,
        max_iterations: int = 30,
        _current_depth: int = 0,
        **llm_kwargs: Any
    ):
        """
        Initialize RLM.

        Args:
            model: Model name (e.g., "gpt-4o", "claude-sonnet-4", "ollama/llama3.2")
            recursive_model: Optional cheaper model for recursive calls
            api_base: Optional API base URL
            api_key: Optional API key
            max_depth: Maximum recursion depth
            max_iterations: Maximum REPL iterations per call
            _current_depth: Internal current depth tracker
            **llm_kwargs: Additional LiteLLM parameters
        """
        self.model = model
        self.recursive_model = recursive_model or model
        self.api_base = api_base
        self.api_key = api_key
        self.max_depth = max_depth
        self.max_iterations = max_iterations
        self._current_depth = _current_depth
        self.llm_kwargs = llm_kwargs

        self.repl = REPLExecutor()

        # Stats
        self._llm_calls = 0
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._reasoning_tokens = 0
        self._iterations = 0
        self._reasoning_traces: list = []

    def complete(
        self,
        query: str = "",
        context: str = "",
        **kwargs: Any
    ) -> str:
        """
        Sync wrapper for acomplete.

        Args:
            query: User query (optional if query is in context)
            context: Context to process (optional, can pass query here)
            **kwargs: Additional LiteLLM parameters

        Returns:
            Final answer string

        Examples:
            # Standard usage
            rlm.complete(query="Summarize this", context=document)

            # Query in context (RLM will extract task)
            rlm.complete(context="Summarize this document: ...")

            # Single string (treat as context)
            rlm.complete("Process this text and extract dates")
        """
        # If only one argument provided, treat it as context
        if query and not context:
            context = query
            query = ""

        return asyncio.run(self.acomplete(query, context, **kwargs))

    async def acomplete(
        self,
        query: str = "",
        context: str = "",
        **kwargs: Any
    ) -> str:
        """
        Main async complete method.

        Args:
            query: User query (optional if query is in context)
            context: Context to process (optional, can pass query here)
            **kwargs: Additional LiteLLM parameters

        Returns:
            Final answer string

        Raises:
            MaxIterationsError: If max iterations exceeded
            MaxDepthError: If max recursion depth exceeded

        Examples:
            # Explicit query and context
            await rlm.acomplete(query="What is this?", context=doc)

            # Query embedded in context
            await rlm.acomplete(context="Extract all dates from: ...")

            # LLM will figure out the task
            await rlm.acomplete(context=document_with_instructions)
        """
        # If only query provided, treat it as context
        if query and not context:
            context = query
            query = ""
        if self._current_depth >= self.max_depth:
            raise MaxDepthError(f"Max recursion depth ({self.max_depth}) exceeded")

        # Initialize REPL environment
        repl_env = self._build_repl_env(query, context)

        # Build initial messages
        system_prompt = build_system_prompt(len(context), self._current_depth)
        messages: List[Message] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # Main loop
        for iteration in range(self.max_iterations):
            self._iterations = iteration + 1

            # Call LLM
            response = await self._call_llm(messages, **kwargs)
            print("\n" + "=" * 80)
            print(f"RLM ITERATION {iteration}")
            print("MODEL RESPONSE:")
            print(response)
            print("=" * 80 + "\n")

            # Check for FINAL
            if is_final(response):
                answer = parse_response(response, repl_env)
                if answer is not None:
                    return answer
# --- AZIZ PATCH: Clean Markdown formatting ---
            # --- AZIZ PATCH: Strip Markdown so the REPL doesn't crash ---
            clean_response = response.replace("```python\n", "").replace("```python", "").replace("```", "").strip()

            # Execute code in REPL
            try:
                exec_result = self.repl.execute(clean_response, repl_env)
            except REPLError as e:
                exec_result = f"Error: {str(e)}"
            except Exception as e:
                exec_result = f"Unexpected error: {str(e)}"

            # --- AZIZ PATCH: X-Ray Vision (Print the sandbox output for us) ---
            print("REPL OBSERVATION (What the AI sees):")
            print(exec_result)
            print("-" * 80 + "\n")

            # Add to conversation
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": exec_result})

        raise MaxIterationsError(
            f"Max iterations ({self.max_iterations}) exceeded without FINAL()"
        )

    async def _call_llm(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> str:
        """
        Call LLM API.

        Args:
            messages: Conversation messages
            **kwargs: Additional parameters (can override model here)

        Returns:
            LLM response text
        """
        self._llm_calls += 1

        # Choose model based on depth
        default_model = self.model if self._current_depth == 0 else self.recursive_model

        # Allow override via kwargs
        model = kwargs.pop('model', default_model)

        # Merge kwargs
        call_kwargs = {**self.llm_kwargs, **kwargs}
        if self.api_base:
            call_kwargs['api_base'] = self.api_base
        if self.api_key:
            call_kwargs['api_key'] = self.api_key

        # Responses API exposes reasoning summaries; Chat Completions never does.
        # reasoning_effort (a Chat-Completions-style kwarg) becomes reasoning={"effort", "summary"}.
        reasoning_effort = call_kwargs.pop("reasoning_effort", None)
        reasoning_param = {"summary": "auto"}
        if reasoning_effort:
            reasoning_param["effort"] = reasoning_effort
        call_kwargs["reasoning"] = reasoning_param

        # Call LiteLLM (240s hard timeout at both litellm and asyncio level;
        # was 60s then 120s, still saw 17/500 (3.4%) time out at 120s on
        # reasoning_effort=high with a large accumulated conversation)
        call_kwargs.setdefault("timeout", 240)
        import asyncio as _asyncio
        response = await _asyncio.wait_for(
            litellm.aresponses(model=model, input=messages, **call_kwargs),
            timeout=240,
        )

        # Token accounting (reset per question by the runner)
        usage = getattr(response, "usage", None)
        if usage is not None:
            self._prompt_tokens += getattr(usage, "input_tokens", 0) or 0
            self._completion_tokens += getattr(usage, "output_tokens", 0) or 0
            details = getattr(usage, "output_tokens_details", None)
            self._reasoning_tokens += getattr(details, "reasoning_tokens", 0) or 0

        # Capture the reasoning summary text (if any) for later trace analysis
        for item in getattr(response, "output", None) or []:
            if getattr(item, "type", None) == "reasoning":
                summary_items = getattr(item, "summary", None) or []
                summary_text = "\n".join(
                    getattr(s, "text", "") for s in summary_items if getattr(s, "text", "")
                )
                if summary_text:
                    self._reasoning_traces.append({
                        "iteration": self._iterations,
                        "llm_call": self._llm_calls,
                        "text": summary_text,
                    })

        # Extract final answer text
        return response.output_text

    def _build_repl_env(self, query: str, context: str) -> Dict[str, Any]:
        """
        Build REPL environment.

        Args:
            query: User query
            context: Context string

        Returns:
            Environment dict
        """
        env: Dict[str, Any] = {
            'context': context,
            'query': query,
            'recursive_llm': self._make_recursive_fn(),
            're': re,  # Whitelist re module
        }
        return env

    def _make_recursive_fn(self) -> Any:
        """
        Create recursive LLM function for REPL.

        Returns:
            Async function that can be called from REPL
        """
        async def recursive_llm(sub_query: str, sub_context: str) -> str:
            """
            Recursively process sub-context.

            Args:
                sub_query: Query for sub-context
                sub_context: Sub-context to process

            Returns:
                Answer from recursive call
            """
            if self._current_depth + 1 >= self.max_depth:
                return f"Max recursion depth ({self.max_depth}) reached"

            # Create sub-RLM with increased depth
            sub_rlm = RLM(
                model=self.recursive_model,
                recursive_model=self.recursive_model,
                api_base=self.api_base,
                api_key=self.api_key,
                max_depth=self.max_depth,
                max_iterations=self.max_iterations,
                _current_depth=self._current_depth + 1,
                **self.llm_kwargs
            )

            return await sub_rlm.acomplete(sub_query, sub_context)

        # Wrap in sync function for REPL compatibility
        def sync_recursive_llm(sub_query: str, sub_context: str) -> str:
            """Sync wrapper for recursive_llm."""
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in async context, but REPL is sync
                # Create a new thread to run async code
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        recursive_llm(sub_query, sub_context)
                    )
                    return future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(recursive_llm(sub_query, sub_context))

        return sync_recursive_llm

    @property
    def stats(self) -> Dict[str, int]:
        """Get execution statistics."""
        return {
            'llm_calls': self._llm_calls,
            'iterations': self._iterations,
            'depth': self._current_depth,
        }
