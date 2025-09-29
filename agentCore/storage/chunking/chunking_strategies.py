"""
Advanced chunking strategies for document processing

This module provides multiple chunking strategies optimized for different content types
and use cases, with intelligent overlap and boundary detection.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

@dataclass
class Chunk:
    """Represents a chunk of text with metadata"""
    content: str
    start_idx: int
    end_idx: int
    metadata: Dict[str, Any]
    token_count: Optional[int] = None
    embedding: Optional[List[float]] = None

class ChunkingMethod(Enum):
    """Available chunking methods"""
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    SLIDING_WINDOW = "sliding_window"
    SENTENCE_BASED = "sentence_based"
    PARAGRAPH_BASED = "paragraph_based"
    TOKEN_BASED = "token_based"
    MARKDOWN_AWARE = "markdown_aware"
    CODE_AWARE = "code_aware"

class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies"""

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 **kwargs):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.config = kwargs

    @abstractmethod
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        Split text into chunks

        Args:
            text: Text to be chunked
            metadata: Optional metadata to attach to chunks

        Returns:
            List of text chunks
        """
        pass

    def _count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """Count tokens in text using tiktoken"""
        if not TIKTOKEN_AVAILABLE:
            # Fallback to rough estimation
            return len(text.split()) * 1.3

        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except:
            # Fallback if model not found
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))

    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        # Improved sentence boundary detection
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)

        # Clean and filter sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs from text"""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]

class RecursiveChunker(ChunkingStrategy):
    """
    Recursive text splitter that tries to split on natural boundaries

    Tries splitting in this order:
    1. Paragraphs (\n\n)
    2. Sentences (. ! ?)
    3. Words (spaces)
    4. Characters
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 separators: Optional[List[str]] = None,
                 **kwargs):
        super().__init__(chunk_size, chunk_overlap, **kwargs)

        self.separators = separators or [
            "\n\n",    # Paragraphs
            "\n",      # Lines
            ". ",      # Sentences
            "! ",      # Exclamations
            "? ",      # Questions
            "; ",      # Semicolons
            ", ",      # Commas
            " ",       # Words
            ""         # Characters
        ]

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Recursively split text using natural boundaries"""
        chunks = []
        metadata = metadata or {}

        def _split_text(text: str, start_idx: int = 0) -> List[Chunk]:
            if len(text) <= self.chunk_size:
                return [Chunk(
                    content=text,
                    start_idx=start_idx,
                    end_idx=start_idx + len(text),
                    metadata=metadata,
                    token_count=self._count_tokens(text)
                )]

            # Try each separator
            for separator in self.separators:
                if separator in text:
                    parts = text.split(separator)
                    if len(parts) > 1:
                        return self._combine_parts(parts, separator, start_idx, metadata)

            # If no separator works, split by chunk size
            return [Chunk(
                content=text[:self.chunk_size],
                start_idx=start_idx,
                end_idx=start_idx + self.chunk_size,
                metadata=metadata,
                token_count=self._count_tokens(text[:self.chunk_size])
            )]

        def _combine_parts(parts: List[str], separator: str, start_idx: int, metadata: Dict) -> List[Chunk]:
            """Combine parts into chunks with overlap"""
            chunks = []
            current_chunk = ""
            current_start = start_idx

            for i, part in enumerate(parts):
                if len(current_chunk + separator + part) <= self.chunk_size:
                    if current_chunk:
                        current_chunk += separator
                    current_chunk += part
                else:
                    if current_chunk:
                        # Add current chunk
                        chunks.append(Chunk(
                            content=current_chunk,
                            start_idx=current_start,
                            end_idx=current_start + len(current_chunk),
                            metadata=metadata,
                            token_count=self._count_tokens(current_chunk)
                        ))

                        # Calculate overlap for next chunk
                        if self.chunk_overlap > 0:
                            overlap_text = current_chunk[-self.chunk_overlap:]
                            current_chunk = overlap_text + separator + part
                            current_start = current_start + len(current_chunk) - len(overlap_text) - len(separator)
                        else:
                            current_chunk = part
                            current_start = current_start + len(current_chunk)
                    else:
                        current_chunk = part

            # Add final chunk
            if current_chunk:
                chunks.append(Chunk(
                    content=current_chunk,
                    start_idx=current_start,
                    end_idx=current_start + len(current_chunk),
                    metadata=metadata,
                    token_count=self._count_tokens(current_chunk)
                ))

            return chunks

        return _split_text(text)

class SemanticChunker(ChunkingStrategy):
    """
    Semantic chunking based on sentence similarity
    Groups semantically similar sentences together
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 100,
                 similarity_threshold: float = 0.7,
                 model_name: str = "all-MiniLM-L6-v2",
                 **kwargs):
        super().__init__(chunk_size, chunk_overlap, **kwargs)

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers required for semantic chunking. Install: pip install sentence-transformers")

        self.similarity_threshold = similarity_threshold
        self.model = SentenceTransformer(model_name)

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Split text based on semantic similarity"""
        sentences = self._extract_sentences(text)

        if len(sentences) <= 1:
            return [Chunk(
                content=text,
                start_idx=0,
                end_idx=len(text),
                metadata=metadata or {},
                token_count=self._count_tokens(text)
            )]

        # Get sentence embeddings
        embeddings = self.model.encode(sentences)

        # Group similar sentences
        chunks = []
        current_chunk = [sentences[0]]
        current_start_idx = 0

        for i in range(1, len(sentences)):
            # Calculate similarity with current chunk
            current_chunk_embedding = self.model.encode([' '.join(current_chunk)])
            sentence_embedding = embeddings[i:i+1]

            similarity = self.model.similarity(current_chunk_embedding, sentence_embedding)[0][0]

            current_chunk_text = ' '.join(current_chunk + [sentences[i]])

            # Add to current chunk if similar and within size limit
            if (similarity >= self.similarity_threshold and
                len(current_chunk_text) <= self.chunk_size):
                current_chunk.append(sentences[i])
            else:
                # Finalize current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(Chunk(
                    content=chunk_text,
                    start_idx=current_start_idx,
                    end_idx=current_start_idx + len(chunk_text),
                    metadata=metadata or {},
                    token_count=self._count_tokens(chunk_text)
                ))

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_sentences = current_chunk[-1:]  # Take last sentence as overlap
                    current_chunk = overlap_sentences + [sentences[i]]
                else:
                    current_chunk = [sentences[i]]

                current_start_idx = current_start_idx + len(chunk_text)

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(Chunk(
                content=chunk_text,
                start_idx=current_start_idx,
                end_idx=current_start_idx + len(chunk_text),
                metadata=metadata or {},
                token_count=self._count_tokens(chunk_text)
            ))

        return chunks

class SlidingWindowChunker(ChunkingStrategy):
    """
    Sliding window chunker with configurable stride
    Good for dense information where context is crucial
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 stride: int = 500,  # How much to move window each time
                 **kwargs):
        super().__init__(chunk_size, 0, **kwargs)  # No overlap needed with sliding window
        self.stride = stride

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Create overlapping chunks with sliding window"""
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]

            chunks.append(Chunk(
                content=chunk_text,
                start_idx=start,
                end_idx=end,
                metadata=metadata or {},
                token_count=self._count_tokens(chunk_text)
            ))

            start += self.stride

            # Stop if we've covered the text
            if end >= len(text):
                break

        return chunks

class MarkdownAwareChunker(ChunkingStrategy):
    """
    Markdown-aware chunker that respects document structure
    Keeps headers with their content
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 100,
                 **kwargs):
        super().__init__(chunk_size, chunk_overlap, **kwargs)

        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Split markdown text preserving structure"""
        # Find all headers
        headers = list(self.header_pattern.finditer(text))

        if not headers:
            # No headers found, use recursive chunking
            recursive_chunker = RecursiveChunker(self.chunk_size, self.chunk_overlap)
            return recursive_chunker.chunk(text, metadata)

        chunks = []

        for i, header_match in enumerate(headers):
            start_idx = header_match.start()

            # Find end of this section (next header or end of text)
            if i < len(headers) - 1:
                end_idx = headers[i + 1].start()
            else:
                end_idx = len(text)

            section_text = text[start_idx:end_idx].strip()
            header_level = len(header_match.group(1))
            header_title = header_match.group(2)

            # Add header info to metadata
            section_metadata = (metadata or {}).copy()
            section_metadata.update({
                'header_level': header_level,
                'header_title': header_title,
                'section_type': 'markdown_section'
            })

            # If section is small enough, keep as single chunk
            if len(section_text) <= self.chunk_size:
                chunks.append(Chunk(
                    content=section_text,
                    start_idx=start_idx,
                    end_idx=end_idx,
                    metadata=section_metadata,
                    token_count=self._count_tokens(section_text)
                ))
            else:
                # Split large sections while preserving header
                header_text = header_match.group(0)
                content_text = section_text[len(header_text):].strip()

                # Split content recursively
                recursive_chunker = RecursiveChunker(
                    self.chunk_size - len(header_text),
                    self.chunk_overlap
                )
                content_chunks = recursive_chunker.chunk(content_text, section_metadata)

                # Prepend header to each chunk
                for chunk in content_chunks:
                    chunk.content = header_text + "\n\n" + chunk.content
                    chunk.start_idx += start_idx
                    chunk.end_idx += start_idx
                    chunk.token_count = self._count_tokens(chunk.content)

                chunks.extend(content_chunks)

        return chunks

class CodeAwareChunker(ChunkingStrategy):
    """
    Code-aware chunker that respects programming language structure
    Keeps functions and classes together when possible
    """

    def __init__(self,
                 chunk_size: int = 2000,  # Larger default for code
                 chunk_overlap: int = 200,
                 language: str = "python",
                 **kwargs):
        super().__init__(chunk_size, chunk_overlap, **kwargs)
        self.language = language.lower()

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Split code text preserving structure"""

        if self.language == "python":
            return self._chunk_python(text, metadata)
        elif self.language in ["javascript", "typescript", "js", "ts"]:
            return self._chunk_javascript(text, metadata)
        else:
            # Fallback to recursive chunking for unknown languages
            recursive_chunker = RecursiveChunker(self.chunk_size, self.chunk_overlap)
            return recursive_chunker.chunk(text, metadata)

    def _chunk_python(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Python-specific chunking"""
        # Pattern for Python functions and classes
        function_pattern = re.compile(r'^(def\s+\w+\(.*?\):.*?)(?=\n\S|\n*$)', re.MULTILINE | re.DOTALL)
        class_pattern = re.compile(r'^(class\s+\w+.*?:.*?)(?=\n\S|\n*$)', re.MULTILINE | re.DOTALL)

        chunks = []
        remaining_text = text
        current_pos = 0

        # Find all functions and classes
        all_blocks = []

        for match in function_pattern.finditer(text):
            all_blocks.append(('function', match.start(), match.end(), match.group(1)))

        for match in class_pattern.finditer(text):
            all_blocks.append(('class', match.start(), match.end(), match.group(1)))

        # Sort by position
        all_blocks.sort(key=lambda x: x[1])

        for block_type, start, end, content in all_blocks:
            # Add any text before this block
            if start > current_pos:
                before_text = text[current_pos:start].strip()
                if before_text:
                    chunks.append(Chunk(
                        content=before_text,
                        start_idx=current_pos,
                        end_idx=start,
                        metadata=(metadata or {}).copy(),
                        token_count=self._count_tokens(before_text)
                    ))

            # Add the block
            block_metadata = (metadata or {}).copy()
            block_metadata.update({
                'code_block_type': block_type,
                'language': self.language
            })

            if len(content) <= self.chunk_size:
                chunks.append(Chunk(
                    content=content,
                    start_idx=start,
                    end_idx=end,
                    metadata=block_metadata,
                    token_count=self._count_tokens(content)
                ))
            else:
                # Split large blocks
                recursive_chunker = RecursiveChunker(self.chunk_size, self.chunk_overlap)
                sub_chunks = recursive_chunker.chunk(content, block_metadata)
                for sub_chunk in sub_chunks:
                    sub_chunk.start_idx += start
                    sub_chunk.end_idx += start
                chunks.extend(sub_chunks)

            current_pos = end

        # Add any remaining text
        if current_pos < len(text):
            remaining = text[current_pos:].strip()
            if remaining:
                chunks.append(Chunk(
                    content=remaining,
                    start_idx=current_pos,
                    end_idx=len(text),
                    metadata=(metadata or {}).copy(),
                    token_count=self._count_tokens(remaining)
                ))

        return chunks

    def _chunk_javascript(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """JavaScript-specific chunking"""
        # Similar implementation for JavaScript
        # This is a simplified version
        recursive_chunker = RecursiveChunker(self.chunk_size, self.chunk_overlap)
        return recursive_chunker.chunk(text, metadata)

def get_chunking_strategy(method: ChunkingMethod, **kwargs) -> ChunkingStrategy:
    """
    Factory function to get chunking strategy

    Args:
        method: Chunking method to use
        **kwargs: Configuration parameters

    Returns:
        Configured chunking strategy
    """

    strategies = {
        ChunkingMethod.RECURSIVE: RecursiveChunker,
        ChunkingMethod.SEMANTIC: SemanticChunker,
        ChunkingMethod.SLIDING_WINDOW: SlidingWindowChunker,
        ChunkingMethod.MARKDOWN_AWARE: MarkdownAwareChunker,
        ChunkingMethod.CODE_AWARE: CodeAwareChunker,
    }

    if method not in strategies:
        raise ValueError(f"Unsupported chunking method: {method}")

    return strategies[method](**kwargs)