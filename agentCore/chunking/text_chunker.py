"""
Advanced text chunking strategies for processing large documents and API responses
"""

import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import tiktoken

from ..logger.logger import get_logger

logger = get_logger("text_chunker")

class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"
    ADAPTIVE = "adaptive"
    TOKEN_BASED = "token_based"

@dataclass
class Chunk:
    """Represents a text chunk"""
    id: str
    content: str
    start_index: int
    end_index: int
    metadata: Dict[str, Any]
    token_count: Optional[int] = None
    overlap_with_previous: bool = False

@dataclass
class ChunkingResult:
    """Result of chunking operation"""
    chunks: List[Chunk]
    total_chunks: int
    strategy_used: ChunkingStrategy
    original_length: int
    total_tokens: Optional[int]
    metadata: Dict[str, Any]

class TextChunker:
    """
    Advanced text chunker with multiple strategies for handling large texts
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 overlap: int = 100,
                 model_name: str = "gpt-3.5-turbo"):
        """
        Initialize text chunker

        Args:
            chunk_size: Target size for chunks (in characters or tokens)
            overlap: Overlap between chunks
            model_name: Model name for token counting
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.model_name = model_name

        # Initialize tokenizer for token-based chunking
        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except:
            # Fallback to cl100k_base encoding
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def chunk_text(self,
                   text: str,
                   strategy: ChunkingStrategy = ChunkingStrategy.ADAPTIVE,
                   metadata: Optional[Dict] = None) -> ChunkingResult:
        """
        Chunk text using specified strategy

        Args:
            text: Text to chunk
            strategy: Chunking strategy to use
            metadata: Additional metadata for chunks

        Returns:
            ChunkingResult with processed chunks
        """
        logger.info(f"📄 Chunking text ({len(text)} chars) using {strategy.value} strategy")

        # Choose chunking method based on strategy
        if strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(text, metadata or {})
        elif strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(text, metadata or {})
        elif strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(text, metadata or {})
        elif strategy == ChunkingStrategy.TOKEN_BASED:
            chunks = self._chunk_by_tokens(text, metadata or {})
        elif strategy == ChunkingStrategy.ADAPTIVE:
            chunks = self._chunk_adaptive(text, metadata or {})
        else:
            # Default to fixed size
            chunks = self._chunk_fixed_size(text, metadata or {})

        # Calculate total tokens
        total_tokens = sum(chunk.token_count for chunk in chunks if chunk.token_count)

        result = ChunkingResult(
            chunks=chunks,
            total_chunks=len(chunks),
            strategy_used=strategy,
            original_length=len(text),
            total_tokens=total_tokens,
            metadata=metadata or {}
        )

        logger.success(f"✅ Created {len(chunks)} chunks (total tokens: {total_tokens})")
        return result

    def _chunk_fixed_size(self, text: str, metadata: Dict) -> List[Chunk]:
        """Chunk by fixed character size with overlap"""
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Adjust end to avoid cutting words
            if end < len(text) and not text[end].isspace():
                # Find last space before end
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space

            chunk_content = text[start:end]
            token_count = len(self.tokenizer.encode(chunk_content))

            chunk = Chunk(
                id=f"chunk_{chunk_id}",
                content=chunk_content,
                start_index=start,
                end_index=end,
                metadata={**metadata, "chunk_method": "fixed_size"},
                token_count=token_count,
                overlap_with_previous=start > 0 and self.overlap > 0
            )

            chunks.append(chunk)

            # Move start position with overlap
            start = max(end - self.overlap, start + 1)
            chunk_id += 1

        return chunks

    def _chunk_by_sentence(self, text: str, metadata: Dict) -> List[Chunk]:
        """Chunk by sentences, respecting size limits"""
        # Split into sentences
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = ""
        start_index = 0
        chunk_id = 0

        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence

            if len(potential_chunk) > self.chunk_size and current_chunk:
                # Create chunk with current content
                token_count = len(self.tokenizer.encode(current_chunk))

                chunk = Chunk(
                    id=f"sentence_chunk_{chunk_id}",
                    content=current_chunk.strip(),
                    start_index=start_index,
                    end_index=start_index + len(current_chunk),
                    metadata={**metadata, "chunk_method": "sentence"},
                    token_count=token_count
                )

                chunks.append(chunk)

                # Start new chunk
                start_index += len(current_chunk)
                current_chunk = sentence
                chunk_id += 1
            else:
                current_chunk = potential_chunk

        # Add final chunk
        if current_chunk:
            token_count = len(self.tokenizer.encode(current_chunk))

            chunk = Chunk(
                id=f"sentence_chunk_{chunk_id}",
                content=current_chunk.strip(),
                start_index=start_index,
                end_index=start_index + len(current_chunk),
                metadata={**metadata, "chunk_method": "sentence"},
                token_count=token_count
            )

            chunks.append(chunk)

        return chunks

    def _chunk_by_paragraph(self, text: str, metadata: Dict) -> List[Chunk]:
        """Chunk by paragraphs, splitting large paragraphs if needed"""
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        chunk_id = 0
        current_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(paragraph) <= self.chunk_size:
                # Paragraph fits in one chunk
                token_count = len(self.tokenizer.encode(paragraph))

                chunk = Chunk(
                    id=f"para_chunk_{chunk_id}",
                    content=paragraph,
                    start_index=current_index,
                    end_index=current_index + len(paragraph),
                    metadata={**metadata, "chunk_method": "paragraph", "is_complete_paragraph": True},
                    token_count=token_count
                )

                chunks.append(chunk)
                chunk_id += 1
            else:
                # Split large paragraph using sentence-based chunking
                para_chunks = self._chunk_by_sentence(paragraph, {**metadata, "large_paragraph": True})

                for i, para_chunk in enumerate(para_chunks):
                    para_chunk.id = f"para_chunk_{chunk_id}_{i}"
                    para_chunk.start_index += current_index
                    para_chunk.end_index += current_index
                    chunks.append(para_chunk)

                chunk_id += len(para_chunks)

            current_index += len(paragraph) + 2  # +2 for newlines

        return chunks

    def _chunk_by_tokens(self, text: str, metadata: Dict) -> List[Chunk]:
        """Chunk by token count"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        chunk_id = 0

        start_token = 0
        while start_token < len(tokens):
            end_token = min(start_token + self.chunk_size, len(tokens))

            # Get chunk tokens
            chunk_tokens = tokens[start_token:end_token]

            # Decode back to text
            chunk_content = self.tokenizer.decode(chunk_tokens)

            # Find character positions (approximate)
            start_char = len(self.tokenizer.decode(tokens[:start_token]))
            end_char = len(self.tokenizer.decode(tokens[:end_token]))

            chunk = Chunk(
                id=f"token_chunk_{chunk_id}",
                content=chunk_content,
                start_index=start_char,
                end_index=end_char,
                metadata={**metadata, "chunk_method": "token_based"},
                token_count=len(chunk_tokens),
                overlap_with_previous=start_token > 0 and self.overlap > 0
            )

            chunks.append(chunk)

            # Move start position with overlap
            overlap_tokens = min(self.overlap, len(chunk_tokens) // 2)
            start_token = end_token - overlap_tokens
            chunk_id += 1

        return chunks

    def _chunk_adaptive(self, text: str, metadata: Dict) -> List[Chunk]:
        """Adaptive chunking that chooses best strategy based on content"""
        # Analyze text characteristics
        analysis = self._analyze_text(text)

        # Choose strategy based on analysis
        if analysis["has_clear_paragraphs"] and analysis["avg_paragraph_length"] < self.chunk_size * 1.5:
            return self._chunk_by_paragraph(text, {**metadata, "adaptive_choice": "paragraph"})
        elif analysis["has_clear_sentences"] and analysis["avg_sentence_length"] < self.chunk_size / 2:
            return self._chunk_by_sentence(text, {**metadata, "adaptive_choice": "sentence"})
        else:
            return self._chunk_by_tokens(text, {**metadata, "adaptive_choice": "token_based"})

    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text to determine best chunking strategy"""
        # Count paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Count sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Calculate metrics
        has_clear_paragraphs = len(paragraphs) > 1 and len(paragraphs) < len(text) / 100
        has_clear_sentences = len(sentences) > 5

        avg_paragraph_length = sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0

        return {
            "has_clear_paragraphs": has_clear_paragraphs,
            "has_clear_sentences": has_clear_sentences,
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
            "avg_paragraph_length": avg_paragraph_length,
            "avg_sentence_length": avg_sentence_length,
            "total_length": len(text)
        }

    def chunk_api_response(self, response_data: Union[str, Dict, List]) -> ChunkingResult:
        """
        Chunk API response data

        Args:
            response_data: API response to chunk

        Returns:
            ChunkingResult with processed chunks
        """
        # Convert response to string if needed
        if isinstance(response_data, (dict, list)):
            import json
            text = json.dumps(response_data, indent=2, ensure_ascii=False)
        else:
            text = str(response_data)

        # Use token-based chunking for API responses (more predictable)
        return self.chunk_text(
            text,
            strategy=ChunkingStrategy.TOKEN_BASED,
            metadata={"content_type": "api_response"}
        )

    def chunk_with_context_preservation(self, text: str, context_markers: List[str]) -> ChunkingResult:
        """
        Chunk text while preserving important context markers

        Args:
            text: Text to chunk
            context_markers: List of important markers to preserve (e.g., headers, section titles)

        Returns:
            ChunkingResult with context-preserved chunks
        """
        chunks = []
        chunk_id = 0

        # Find all context markers
        marker_positions = []
        for marker in context_markers:
            for match in re.finditer(re.escape(marker), text, re.IGNORECASE):
                marker_positions.append((match.start(), match.end(), marker))

        # Sort by position
        marker_positions.sort()

        if not marker_positions:
            # No markers found, use adaptive chunking
            return self.chunk_text(text, ChunkingStrategy.ADAPTIVE)

        current_pos = 0

        for i, (start_pos, end_pos, marker) in enumerate(marker_positions):
            # Create chunk for content before marker
            if start_pos > current_pos:
                content = text[current_pos:start_pos].strip()
                if content:
                    token_count = len(self.tokenizer.encode(content))

                    chunk = Chunk(
                        id=f"context_chunk_{chunk_id}",
                        content=content,
                        start_index=current_pos,
                        end_index=start_pos,
                        metadata={"chunk_method": "context_preserved", "before_marker": marker},
                        token_count=token_count
                    )

                    chunks.append(chunk)
                    chunk_id += 1

            # Determine content for chunk starting with marker
            next_marker_pos = marker_positions[i + 1][0] if i + 1 < len(marker_positions) else len(text)

            # Take content from marker to next marker or end, respecting chunk size
            marker_content_end = min(end_pos + self.chunk_size, next_marker_pos)
            marker_content = text[start_pos:marker_content_end]

            token_count = len(self.tokenizer.encode(marker_content))

            chunk = Chunk(
                id=f"context_chunk_{chunk_id}",
                content=marker_content,
                start_index=start_pos,
                end_index=marker_content_end,
                metadata={"chunk_method": "context_preserved", "contains_marker": marker},
                token_count=token_count
            )

            chunks.append(chunk)
            chunk_id += 1

            current_pos = marker_content_end

        # Handle remaining text
        if current_pos < len(text):
            remaining_content = text[current_pos:].strip()
            if remaining_content:
                token_count = len(self.tokenizer.encode(remaining_content))

                chunk = Chunk(
                    id=f"context_chunk_{chunk_id}",
                    content=remaining_content,
                    start_index=current_pos,
                    end_index=len(text),
                    metadata={"chunk_method": "context_preserved", "final_chunk": True},
                    token_count=token_count
                )

                chunks.append(chunk)

        return ChunkingResult(
            chunks=chunks,
            total_chunks=len(chunks),
            strategy_used=ChunkingStrategy.ADAPTIVE,
            original_length=len(text),
            total_tokens=sum(chunk.token_count for chunk in chunks if chunk.token_count),
            metadata={"context_markers": context_markers}
        )

    def optimize_for_retrieval(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Optimize chunks for better retrieval performance

        Args:
            chunks: Original chunks

        Returns:
            Optimized chunks
        """
        optimized_chunks = []

        for chunk in chunks:
            # Add summary or key information to chunk metadata
            summary = self._generate_chunk_summary(chunk.content)

            optimized_chunk = Chunk(
                id=chunk.id,
                content=chunk.content,
                start_index=chunk.start_index,
                end_index=chunk.end_index,
                metadata={
                    **chunk.metadata,
                    "summary": summary,
                    "optimized_for_retrieval": True
                },
                token_count=chunk.token_count,
                overlap_with_previous=chunk.overlap_with_previous
            )

            optimized_chunks.append(optimized_chunk)

        return optimized_chunks

    def _generate_chunk_summary(self, content: str) -> str:
        """Generate a brief summary of chunk content"""
        # Extract first sentence or first 100 characters as summary
        sentences = re.split(r'[.!?]+', content)
        first_sentence = sentences[0].strip() if sentences else ""

        if len(first_sentence) > 100:
            return content[:100] + "..."
        elif first_sentence:
            return first_sentence
        else:
            return content[:50] + "..."