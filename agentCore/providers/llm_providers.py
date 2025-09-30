"""
Módulo para gerenciar diferentes provedores LLM de forma componentizada.
Suporta AWS Bedrock (principal), Ollama, OpenAI e Google Gemini.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Union

class LLMProvider(ABC):
    @abstractmethod
    def get_llm(self): pass
    @abstractmethod
    def get_embeddings(self): pass

class BedrockProvider(LLMProvider):
    # ... (o conteúdo desta classe não precisa de ser alterado)
    def __init__(self):
        self.region_name = os.getenv("AWS_REGION", "us-east-1")
        self.model = os.getenv("BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0")
        self.embeddings_model = os.getenv("BEDROCK_EMBEDDINGS_MODEL", "amazon.titan-embed-text-v1")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    def get_llm(self):
        try:
            from langchain_aws import ChatBedrock
            credentials = {}
            if self.aws_access_key_id: credentials["aws_access_key_id"] = self.aws_access_key_id
            if self.aws_secret_access_key: credentials["aws_secret_access_key"] = self.aws_secret_access_key
            if self.aws_session_token: credentials["aws_session_token"] = self.aws_session_token
            return ChatBedrock(model_id=self.model, region_name=self.region_name, **credentials)
        except ImportError:
            raise ImportError("langchain-aws não está instalado. Execute: pip install langchain-aws boto3")
    def get_embeddings(self):
        try:
            from langchain_aws import BedrockEmbeddings
            credentials = {}
            if self.aws_access_key_id: credentials["aws_access_key_id"] = self.aws_access_key_id
            if self.aws_secret_access_key: credentials["aws_secret_access_key"] = self.aws_secret_access_key
            if self.aws_session_token: credentials["aws_session_token"] = self.aws_session_token
            return BedrockEmbeddings(model_id=self.embeddings_model, region_name=self.region_name, **credentials)
        except ImportError:
            raise ImportError("langchain-aws não está instalado. Execute: pip install langchain-aws boto3")

class OllamaProvider(LLMProvider):
    """Provedor para Ollama - Para desenvolvimento local."""
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3:latest")
        self.embeddings_model = os.getenv("OLLAMA_EMBEDDINGS_MODEL", "nomic-embed-text")

    def get_llm(self):
        try:
            # --- VOLTAMOS À VERSÃO CORRETA E SIMPLES ---
            from langchain_ollama import ChatOllama
            return ChatOllama(model=self.model, base_url=self.base_url)
        except ImportError:
            raise ImportError("langchain-community e langchain-ollama não estão instalados.")

    def get_embeddings(self):
        try:
            from langchain_community.embeddings import OllamaEmbeddings
            return OllamaEmbeddings(model=self.embeddings_model, base_url=self.base_url)
        except ImportError:
            raise ImportError("langchain-community e langchain-ollama não estão instalados.")

class OpenAIProvider(LLMProvider):
    # ... (o conteúdo desta classe não precisa de ser alterado)
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        if not self.api_key: raise ValueError("OPENAI_API_KEY não configurada.")
    def get_llm(self):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=self.model, api_key=self.api_key)
        except ImportError:
            raise ImportError("langchain-openai não está instalado.")
    def get_embeddings(self):
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(api_key=self.api_key)
        except ImportError:
            raise ImportError("langchain-openai não está instalado.")

class GeminiProvider(LLMProvider):
    # ... (o conteúdo desta classe não precisa de ser alterado)
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if not self.api_key: raise ValueError("GEMINI_API_KEY não configurada.")
    def get_llm(self):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=self.model, google_api_key=self.api_key)
        except ImportError:
            raise ImportError("langchain-google-genai não está instalado.")
    def get_embeddings(self):
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(google_api_key=self.api_key)
        except ImportError:
            raise ImportError("langchain-google-genai não está instalado.")

class LLMFactory:
    @staticmethod
    def create_provider(provider_name: Optional[str] = None) -> LLMProvider:
        if provider_name is None:
            provider_name = os.getenv("MAIN_PROVIDER", "bedrock").lower()
        providers = {"bedrock": BedrockProvider, "ollama": OllamaProvider, "openai": OpenAIProvider, "gemini": GeminiProvider}
        if provider_name not in providers:
            raise ValueError(f"Provedor '{provider_name}' não suportado.")
        try:
            return providers[provider_name]()
        except Exception as e:
            raise ValueError(f"Erro ao inicializar provedor '{provider_name}': {str(e)}")

def get_llm(provider_name: Optional[str] = None, provider: Optional[str] = None,
           model: Optional[str] = None, temperature: Optional[float] = None,
           max_tokens: Optional[int] = None):
    """
    Cria um LLM com configurações personalizadas.

    Args:
        provider_name: Nome do provedor (backward compatibility)
        provider: Nome do provedor (novo parâmetro)
        model: Modelo específico a usar
        temperature: Temperatura para geração
        max_tokens: Máximo de tokens
    """
    # Usar 'provider' se fornecido, senão usar 'provider_name'
    provider_to_use = provider if provider is not None else provider_name

    provider_instance = LLMFactory.create_provider(provider_to_use)

    # Para diferentes provedores, aplicar configurações específicas
    if provider_to_use == "ollama":
        return _create_ollama_llm(provider_instance, model, temperature, max_tokens)
    elif provider_to_use == "openai":
        return _create_openai_llm(provider_instance, model, temperature, max_tokens)
    elif provider_to_use == "gemini":
        return _create_gemini_llm(provider_instance, model, temperature, max_tokens)
    elif provider_to_use == "bedrock":
        return _create_bedrock_llm(provider_instance, model, temperature, max_tokens)
    else:
        # Fallback para comportamento padrão
        return provider_instance.get_llm()

def _create_ollama_llm(provider_instance, model=None, temperature=None, max_tokens=None):
    """Cria LLM Ollama com configurações personalizadas."""
    try:
        from langchain_ollama import ChatOllama

        kwargs = {
            "model": model or provider_instance.model,
            "base_url": provider_instance.base_url
        }

        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["num_predict"] = max_tokens  # Ollama usa 'num_predict'

        return ChatOllama(**kwargs)
    except ImportError:
        raise ImportError("langchain-community e langchain-ollama não estão instalados.")

def _create_openai_llm(provider_instance, model=None, temperature=None, max_tokens=None):
    """Cria LLM OpenAI com configurações personalizadas."""
    try:
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model or provider_instance.model,
            "api_key": provider_instance.api_key
        }

        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        return ChatOpenAI(**kwargs)
    except ImportError:
        raise ImportError("langchain-openai não está instalado.")

def _create_gemini_llm(provider_instance, model=None, temperature=None, max_tokens=None):
    """Cria LLM Gemini com configurações personalizadas."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        kwargs = {
            "model": model or provider_instance.model,
            "google_api_key": provider_instance.api_key
        }

        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_output_tokens"] = max_tokens  # Gemini usa 'max_output_tokens'

        return ChatGoogleGenerativeAI(**kwargs)
    except ImportError:
        raise ImportError("langchain-google-genai não está instalado.")

def _create_bedrock_llm(provider_instance, model=None, temperature=None, max_tokens=None):
    """Cria LLM Bedrock com configurações personalizadas."""
    try:
        from langchain_aws import ChatBedrock

        credentials = {}
        if provider_instance.aws_access_key_id:
            credentials["aws_access_key_id"] = provider_instance.aws_access_key_id
        if provider_instance.aws_secret_access_key:
            credentials["aws_secret_access_key"] = provider_instance.aws_secret_access_key
        if provider_instance.aws_session_token:
            credentials["aws_session_token"] = provider_instance.aws_session_token

        kwargs = {
            "model_id": model or provider_instance.model,
            "region_name": provider_instance.region_name,
            **credentials
        }

        # Bedrock usa model_kwargs para configurações específicas
        model_kwargs = {}
        if temperature is not None:
            model_kwargs["temperature"] = temperature
        if max_tokens is not None:
            model_kwargs["max_tokens"] = max_tokens

        if model_kwargs:
            kwargs["model_kwargs"] = model_kwargs

        return ChatBedrock(**kwargs)
    except ImportError:
        raise ImportError("langchain-aws não está instalado. Execute: pip install langchain-aws boto3")

def get_embeddings(provider_name: Optional[str] = None):
    provider = LLMFactory.create_provider(provider_name)
    return provider.get_embeddings()

def get_provider_info(provider_name: Optional[str] = None) -> dict:
    # ... (o conteúdo desta função não precisa de ser alterado)
    if provider_name is None: provider_name = os.getenv("MAIN_PROVIDER", "bedrock").lower()
    provider = LLMFactory.create_provider(provider_name)
    info = {"provider": provider_name}
    if isinstance(provider, BedrockProvider):
        info.update({"region": provider.region_name, "model": provider.model, "embeddings_model": provider.embeddings_model, "credentials_configured": bool(provider.aws_access_key_id or os.getenv("AWS_PROFILE"))})
    elif isinstance(provider, OllamaProvider):
        info.update({"base_url": provider.base_url, "model": provider.model, "embeddings_model": provider.embeddings_model})
    elif isinstance(provider, OpenAIProvider):
        info.update({"model": provider.model, "api_key_configured": bool(provider.api_key)})
    elif isinstance(provider, GeminiProvider):
        info.update({"model": provider.model, "api_key_configured": bool(provider.api_key)})
    return info
