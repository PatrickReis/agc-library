"""
Módulo para gerenciar diferentes provedores LLM de forma componentizada.
Suporta AWS Bedrock (principal), Ollama, OpenAI e Google Gemini.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Union


class LLMProvider(ABC):
    """Classe abstrata para provedores LLM."""

    @abstractmethod
    def get_llm(self):
        """Retorna a instância do LLM."""
        pass

    @abstractmethod
    def get_embeddings(self):
        """Retorna a instância dos embeddings."""
        pass


class BedrockProvider(LLMProvider):
    """Provedor para AWS Bedrock - Principal provedor para produção."""

    def __init__(self):
        self.region_name = os.getenv("AWS_REGION", "us-east-1")
        self.model = os.getenv("BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0")
        self.embeddings_model = os.getenv("BEDROCK_EMBEDDINGS_MODEL", "amazon.titan-embed-text-v1")

        # AWS credentials should be configured via AWS CLI, IAM roles, or environment variables
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token = os.getenv("AWS_SESSION_TOKEN")

    def get_llm(self):
        try:
            from langchain_aws import ChatBedrock

            credentials = {}
            if self.aws_access_key_id:
                credentials["aws_access_key_id"] = self.aws_access_key_id
            if self.aws_secret_access_key:
                credentials["aws_secret_access_key"] = self.aws_secret_access_key
            if self.aws_session_token:
                credentials["aws_session_token"] = self.aws_session_token

            return ChatBedrock(
                model_id=self.model,
                region_name=self.region_name,
                **credentials
            )
        except ImportError:
            raise ImportError("langchain-aws não está instalado. Execute: pip install langchain-aws boto3")

    def get_embeddings(self):
        try:
            from langchain_aws import BedrockEmbeddings

            credentials = {}
            if self.aws_access_key_id:
                credentials["aws_access_key_id"] = self.aws_access_key_id
            if self.aws_secret_access_key:
                credentials["aws_secret_access_key"] = self.aws_secret_access_key
            if self.aws_session_token:
                credentials["aws_session_token"] = self.aws_session_token

            return BedrockEmbeddings(
                model_id=self.embeddings_model,
                region_name=self.region_name,
                **credentials
            )
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
            from langchain_ollama import OllamaLLM
            return OllamaLLM(
                model=self.model,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("langchain-ollama não está instalado. Execute: pip install langchain-ollama")

    def get_embeddings(self):
        try:
            from langchain_ollama import OllamaEmbeddings
            return OllamaEmbeddings(
                model=self.embeddings_model,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("langchain-ollama não está instalado. Execute: pip install langchain-ollama")


class OpenAIProvider(LLMProvider):
    """Provedor para OpenAI."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não configurada no arquivo .env")

    def get_llm(self):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=self.model,
                api_key=self.api_key
            )
        except ImportError:
            raise ImportError("langchain-openai não está instalado. Execute: pip install langchain-openai")

    def get_embeddings(self):
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                api_key=self.api_key
            )
        except ImportError:
            raise ImportError("langchain-openai não está instalado. Execute: pip install langchain-openai")


class GeminiProvider(LLMProvider):
    """Provedor para Google Gemini."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada no arquivo .env")

    def get_llm(self):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key
            )
        except ImportError:
            raise ImportError("langchain-google-genai não está instalado. Execute: pip install langchain-google-genai")

    def get_embeddings(self):
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                google_api_key=self.api_key
            )
        except ImportError:
            raise ImportError("langchain-google-genai não está instalado. Execute: pip install langchain-google-genai")


class LLMFactory:
    """Factory para criar instâncias de provedores LLM."""

    @staticmethod
    def create_provider(provider_name: Optional[str] = None) -> LLMProvider:
        """
        Cria uma instância do provedor LLM especificado.

        Args:
            provider_name: Nome do provedor ('bedrock', 'ollama', 'openai', 'gemini')
                           Se None, usa a variável de ambiente MAIN_PROVIDER

        Returns:
            Instância do provedor LLM

        Raises:
            ValueError: Se o provedor não for suportado ou não estiver configurado
        """
        if provider_name is None:
            # Bedrock é o padrão (principal para produção)
            provider_name = os.getenv("MAIN_PROVIDER", "bedrock").lower()

        providers = {
            "bedrock": BedrockProvider,
            "ollama": OllamaProvider,
            "openai": OpenAIProvider,
            "gemini": GeminiProvider
        }

        if provider_name not in providers:
            raise ValueError(
                f"Provedor '{provider_name}' não suportado. "
                f"Provedores disponíveis: {', '.join(providers.keys())}"
            )

        try:
            return providers[provider_name]()
        except Exception as e:
            raise ValueError(
                f"Erro ao inicializar provedor '{provider_name}': {str(e)}"
            )


# Funções de conveniência para uso direto
def get_llm(provider_name: Optional[str] = None):
    """Retorna a instância do LLM do provedor especificado."""
    provider = LLMFactory.create_provider(provider_name)
    return provider.get_llm()


def get_embeddings(provider_name: Optional[str] = None):
    """Retorna a instância dos embeddings do provedor especificado."""
    provider = LLMFactory.create_provider(provider_name)
    return provider.get_embeddings()


def get_provider_info(provider_name: Optional[str] = None) -> dict:
    """Retorna informações sobre o provedor atual."""
    if provider_name is None:
        provider_name = os.getenv("MAIN_PROVIDER", "bedrock").lower()

    provider = LLMFactory.create_provider(provider_name)

    info = {
        "provider": provider_name,
    }

    # Adicionar informações específicas do provedor
    if isinstance(provider, BedrockProvider):
        info.update({
            "region": provider.region_name,
            "model": provider.model,
            "embeddings_model": provider.embeddings_model,
            "credentials_configured": bool(provider.aws_access_key_id or os.getenv("AWS_PROFILE"))
        })
    elif isinstance(provider, OllamaProvider):
        info.update({
            "base_url": provider.base_url,
            "model": provider.model,
            "embeddings_model": provider.embeddings_model
        })
    elif isinstance(provider, OpenAIProvider):
        info.update({
            "model": provider.model,
            "api_key_configured": bool(provider.api_key)
        })
    elif isinstance(provider, GeminiProvider):
        info.update({
            "model": provider.model,
            "api_key_configured": bool(provider.api_key)
        })

    return info