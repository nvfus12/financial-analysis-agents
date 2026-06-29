import os
import random
import logging
from typing import Generator
import google.generativeai as genai
from src.domain.ports.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class GeminiAdapter(LLMProvider):
    """
    Adapter implementing the LLMProvider interface using Google Generative AI (Gemini).
    Supports load balancing across multiple Gemini API keys and automatic fallback to 9router
    (or vice versa) if any key fails or rate limits are reached.
    """

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name

    def _execute_with_retry(self, operation_fn):
        """
        Executes a generative operation with load balancing and automatic fallback:
        - If primary is native Gemini: shuffles and shunts requests across gemini keys. If all fail, falls back to 9router.
        - If primary is 9router: tries 9router first. If it fails, falls back to native gemini keys list.
        """
        primary = os.getenv("PRIMARY_PROVIDER", "gemini").lower()
        
        # Load multiple Gemini keys
        gemini_keys_str = os.getenv("GEMINI_API_KEYS", "").strip()
        if not gemini_keys_str:
            gemini_keys_str = os.getenv("GEMINI_API_KEY", "").strip()
        gemini_keys = [k.strip() for k in gemini_keys_str.split(",") if k.strip()]
        
        nine_router_key = os.getenv("NINE_ROUTER_API_KEY", "").strip()
        nine_router_base = os.getenv("NINE_ROUTER_API_BASE", "https://api.9router.com/v1").strip()

        # Build list of providers to try in order
        providers_queue = []
        if primary == "9router":
            if nine_router_key:
                providers_queue.append(("9router", nine_router_key, nine_router_base))
            if gemini_keys:
                shuffled_keys = list(gemini_keys)
                random.shuffle(shuffled_keys)
                for key in shuffled_keys:
                    providers_queue.append(("gemini", key, ""))
        else: # Default: native gemini
            if gemini_keys:
                shuffled_keys = list(gemini_keys)
                random.shuffle(shuffled_keys)
                for key in shuffled_keys:
                    providers_queue.append(("gemini", key, ""))
            if nine_router_key:
                providers_queue.append(("9router", nine_router_key, nine_router_base))

        if not providers_queue:
            raise ValueError("No API credentials configured. Please set Google Gemini keys or 9router key in settings.")

        last_exception = None
        for idx, (provider_type, key, base_url) in enumerate(providers_queue):
            try:
                if provider_type == "gemini":
                    logger.info(f"Attempting native Gemini request using key: ...{key[-4:]} (index {idx+1}/{len(providers_queue)})")
                    genai.configure(api_key=key)
                    return operation_fn(use_openai=False, client=None)
                else: # 9router
                    logger.info(f"Attempting 9router request using base: {base_url} (index {idx+1}/{len(providers_queue)})")
                    from openai import OpenAI
                    client = OpenAI(api_key=key, base_url=base_url)
                    return operation_fn(use_openai=True, client=client)
            except Exception as e:
                logger.warning(f"LLM Provider {provider_type} (index {idx+1}) failed with error: {e}. Trying next fallback...")
                last_exception = e
                continue
                
        logger.error("All configured API keys and fallback providers failed.")
        raise last_exception

    def generate_text(self, system_instruction: str, prompt: str, temperature: float = 0.2) -> str:
        """Generates text completion with key load-balancing and fallback."""
        def run(use_openai, client):
            if use_openai:
                model = os.getenv("LLM_MODEL_NAME_OVERRIDE", "").strip()
                if not model:
                    model = f"google/{self.model_name}" if "/" not in self.model_name else self.model_name
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature
                )
                return response.choices[0].message.content or ""
            else:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction
                )
                config = genai.GenerationConfig(temperature=temperature)
                response = model.generate_content(prompt, generation_config=config)
                return response.text

        return self._execute_with_retry(run)

    def generate_stream(self, system_instruction: str, prompt: str, temperature: float = 0.2) -> Generator[str, None, None]:
        """Streams text completion with key load-balancing and fallback."""
        def run(use_openai, client):
            if use_openai:
                model = os.getenv("LLM_MODEL_NAME_OVERRIDE", "").strip()
                if not model:
                    model = f"google/{self.model_name}" if "/" not in self.model_name else self.model_name
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    stream=True
                )
                # Since we must return a generator, we yield chunk text inside the runner context
                # and return the generator object
                def yield_chunks():
                    for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content
                return yield_chunks()
            else:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction
                )
                config = genai.GenerationConfig(temperature=temperature)
                response = model.generate_content(prompt, generation_config=config, stream=True)
                def yield_chunks():
                    for chunk in response:
                        yield chunk.text
                return yield_chunks()

        # To support generators with fallback inside, we fetch the generator and propagate yields
        generator = self._execute_with_retry(run)
        for chunk in generator:
            yield chunk
