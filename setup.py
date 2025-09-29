#!/usr/bin/env python3
"""
Setup configuration for agentCore library
"""

from setuptools import setup, find_packages
import os

# Read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="agentcore",
    version="2.0.0",
    author="AgentCore Team",
    author_email="contact@agentcore.com",
    description="A comprehensive library for building AI agents with tool integration and multi-provider LLM support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/agent-core",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "langchain-core>=0.1.0",
        "langchain-chroma>=0.1.0",
        "langchain-aws>=0.1.0",
        "langchain-openai>=0.1.0",
        "langchain-ollama>=0.1.0",
        "langchain-google-genai>=0.1.0",
        "langgraph>=0.1.0",
        "boto3>=1.34.0",
        "chromadb>=0.4.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "colorlog>=6.7.0",
        "pydantic>=2.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "aws": [
            "boto3>=1.34.0",
            "langchain-aws>=0.1.0",
            "opensearch-py>=2.0.0",
            "requests-aws4auth>=1.1.0",
        ],
        "openai": [
            "langchain-openai>=0.1.0",
        ],
        "ollama": [
            "langchain-ollama>=0.1.0",
        ],
        "google": [
            "langchain-google-genai>=0.1.0",
        ],
        "crewai": [
            "crewai>=0.1.0",
        ],
        "autogen": [
            "pyautogen>=0.2.0",
        ],
        "qdrant": [
            "qdrant-client>=1.6.0",
        ],
        "pinecone": [
            "pinecone-client>=3.0.0",
        ],
        "weaviate": [
            "weaviate-client>=3.25.0",
        ],
        "faiss": [
            "faiss-cpu>=1.7.4",
        ],
        "semantic": [
            "sentence-transformers>=2.2.0",
        ],
        "full": [
            "boto3>=1.34.0",
            "langchain-aws>=0.1.0",
            "opensearch-py>=2.0.0",
            "requests-aws4auth>=1.1.0",
            "crewai>=0.1.0",
            "pyautogen>=0.2.0",
            "qdrant-client>=1.6.0",
            "pinecone-client>=3.0.0",
            "weaviate-client>=3.25.0",
            "faiss-cpu>=1.7.4",
            "sentence-transformers>=2.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agentcore=agentCore.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)