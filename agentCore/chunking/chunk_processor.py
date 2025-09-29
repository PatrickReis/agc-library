"""
Chunk processor for handling chunked content in agent workflows
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import asyncio
import concurrent.futures

from .text_chunker import Chunk, ChunkingResult
from ..logger.logger import get_logger

logger = get_logger("chunk_processor")

@dataclass
class ProcessedChunk:
    """Result of processing a single chunk"""
    original_chunk: Chunk
    processed_content: Any
    success: bool
    error_message: Optional[str] = None
    processing_time_ms: float = 0.0

@dataclass
class ChunkProcessingResult:
    """Result of processing multiple chunks"""
    processed_chunks: List[ProcessedChunk]
    successful_count: int
    failed_count: int
    total_processing_time_ms: float
    aggregated_result: Optional[Any] = None

class ChunkProcessor:
    """
    Process chunks using various strategies (sequential, parallel, streaming)
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize chunk processor

        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers

    def process_chunks_sequential(self,
                                 chunks: List[Chunk],
                                 processor_func: Callable[[Chunk], Any],
                                 progress_callback: Optional[Callable] = None) -> ChunkProcessingResult:
        """
        Process chunks sequentially

        Args:
            chunks: List of chunks to process
            processor_func: Function to process each chunk
            progress_callback: Optional callback for progress updates

        Returns:
            ChunkProcessingResult with processing results
        """
        logger.info(f"🔄 Processing {len(chunks)} chunks sequentially")

        processed_chunks = []
        start_time = time.time()

        for i, chunk in enumerate(chunks):
            chunk_start_time = time.time()

            try:
                result = processor_func(chunk)
                processing_time = (time.time() - chunk_start_time) * 1000

                processed_chunk = ProcessedChunk(
                    original_chunk=chunk,
                    processed_content=result,
                    success=True,
                    processing_time_ms=processing_time
                )

            except Exception as e:
                processing_time = (time.time() - chunk_start_time) * 1000
                logger.warning(f"Failed to process chunk {chunk.id}: {e}")

                processed_chunk = ProcessedChunk(
                    original_chunk=chunk,
                    processed_content=None,
                    success=False,
                    error_message=str(e),
                    processing_time_ms=processing_time
                )

            processed_chunks.append(processed_chunk)

            # Progress callback
            if progress_callback:
                progress_callback(i + 1, len(chunks), processed_chunk)

        total_time = (time.time() - start_time) * 1000

        result = ChunkProcessingResult(
            processed_chunks=processed_chunks,
            successful_count=sum(1 for pc in processed_chunks if pc.success),
            failed_count=sum(1 for pc in processed_chunks if not pc.success),
            total_processing_time_ms=total_time
        )

        logger.success(f"✅ Sequential processing completed: {result.successful_count}/{len(chunks)} successful")
        return result

    def process_chunks_parallel(self,
                               chunks: List[Chunk],
                               processor_func: Callable[[Chunk], Any],
                               progress_callback: Optional[Callable] = None) -> ChunkProcessingResult:
        """
        Process chunks in parallel

        Args:
            chunks: List of chunks to process
            processor_func: Function to process each chunk
            progress_callback: Optional callback for progress updates

        Returns:
            ChunkProcessingResult with processing results
        """
        logger.info(f"⚡ Processing {len(chunks)} chunks in parallel (max_workers={self.max_workers})")

        processed_chunks = []
        start_time = time.time()

        def process_single_chunk(chunk_with_index):
            index, chunk = chunk_with_index
            chunk_start_time = time.time()

            try:
                result = processor_func(chunk)
                processing_time = (time.time() - chunk_start_time) * 1000

                return ProcessedChunk(
                    original_chunk=chunk,
                    processed_content=result,
                    success=True,
                    processing_time_ms=processing_time
                )

            except Exception as e:
                processing_time = (time.time() - chunk_start_time) * 1000

                return ProcessedChunk(
                    original_chunk=chunk,
                    processed_content=None,
                    success=False,
                    error_message=str(e),
                    processing_time_ms=processing_time
                )

        # Process chunks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            chunk_with_indices = [(i, chunk) for i, chunk in enumerate(chunks)]

            # Submit all tasks
            future_to_index = {
                executor.submit(process_single_chunk, chunk_data): chunk_data[0]
                for chunk_data in chunk_with_indices
            }

            # Collect results as they complete
            completed_results = {}
            completed_count = 0

            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                completed_results[index] = future.result()
                completed_count += 1

                # Progress callback
                if progress_callback:
                    progress_callback(completed_count, len(chunks), completed_results[index])

        # Sort results by original order
        processed_chunks = [completed_results[i] for i in range(len(chunks))]

        total_time = (time.time() - start_time) * 1000

        result = ChunkProcessingResult(
            processed_chunks=processed_chunks,
            successful_count=sum(1 for pc in processed_chunks if pc.success),
            failed_count=sum(1 for pc in processed_chunks if not pc.success),
            total_processing_time_ms=total_time
        )

        logger.success(f"✅ Parallel processing completed: {result.successful_count}/{len(chunks)} successful")
        return result

    def process_chunks_streaming(self,
                                chunks: List[Chunk],
                                processor_func: Callable[[Chunk], Any],
                                batch_size: int = 5,
                                result_callback: Optional[Callable] = None) -> ChunkProcessingResult:
        """
        Process chunks in streaming fashion (batches)

        Args:
            chunks: List of chunks to process
            processor_func: Function to process each chunk
            batch_size: Size of each batch
            result_callback: Callback for each completed batch

        Returns:
            ChunkProcessingResult with processing results
        """
        logger.info(f"🌊 Processing {len(chunks)} chunks in streaming batches of {batch_size}")

        all_processed_chunks = []
        start_time = time.time()

        # Process in batches
        for batch_start in range(0, len(chunks), batch_size):
            batch_end = min(batch_start + batch_size, len(chunks))
            batch = chunks[batch_start:batch_end]

            logger.info(f"Processing batch {batch_start//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")

            # Process batch in parallel
            batch_result = self.process_chunks_parallel(batch, processor_func)
            all_processed_chunks.extend(batch_result.processed_chunks)

            # Callback with batch results
            if result_callback:
                result_callback(batch_result, batch_start // batch_size + 1)

        total_time = (time.time() - start_time) * 1000

        result = ChunkProcessingResult(
            processed_chunks=all_processed_chunks,
            successful_count=sum(1 for pc in all_processed_chunks if pc.success),
            failed_count=sum(1 for pc in all_processed_chunks if not pc.success),
            total_processing_time_ms=total_time
        )

        logger.success(f"✅ Streaming processing completed: {result.successful_count}/{len(chunks)} successful")
        return result

    def aggregate_results(self,
                         processing_result: ChunkProcessingResult,
                         aggregation_func: Callable[[List[Any]], Any]) -> ChunkProcessingResult:
        """
        Aggregate processing results

        Args:
            processing_result: Results from chunk processing
            aggregation_func: Function to aggregate successful results

        Returns:
            Updated ChunkProcessingResult with aggregated result
        """
        # Extract successful results
        successful_results = [
            pc.processed_content
            for pc in processing_result.processed_chunks
            if pc.success and pc.processed_content is not None
        ]

        if successful_results:
            try:
                aggregated = aggregation_func(successful_results)
                processing_result.aggregated_result = aggregated
                logger.info(f"📊 Aggregated {len(successful_results)} successful results")
            except Exception as e:
                logger.error(f"Aggregation failed: {e}")

        return processing_result

    def create_llm_processor(self, llm, prompt_template: str) -> Callable[[Chunk], str]:
        """
        Create a processor function for LLM processing

        Args:
            llm: Language model instance
            prompt_template: Template for processing prompts (use {content} placeholder)

        Returns:
            Processor function
        """
        def process_chunk(chunk: Chunk) -> str:
            prompt = prompt_template.format(content=chunk.content)

            try:
                if hasattr(llm, 'invoke'):
                    response = llm.invoke(prompt)
                    return response.content if hasattr(response, 'content') else str(response)
                else:
                    return str(llm(prompt))
            except Exception as e:
                raise Exception(f"LLM processing failed: {e}")

        return process_chunk

    def create_summarization_processor(self, llm) -> Callable[[Chunk], str]:
        """Create a processor for text summarization"""
        template = """
        Summarize the following text in 2-3 sentences, focusing on the main points:

        {content}

        Summary:"""

        return self.create_llm_processor(llm, template)

    def create_analysis_processor(self, llm, analysis_type: str = "general") -> Callable[[Chunk], str]:
        """Create a processor for text analysis"""
        templates = {
            "sentiment": "Analyze the sentiment of this text and provide a brief explanation:\n\n{content}\n\nSentiment Analysis:",
            "topics": "Identify the main topics discussed in this text:\n\n{content}\n\nMain Topics:",
            "keywords": "Extract key terms and phrases from this text:\n\n{content}\n\nKey Terms:",
            "general": "Analyze this text and provide key insights:\n\n{content}\n\nAnalysis:"
        }

        template = templates.get(analysis_type, templates["general"])
        return self.create_llm_processor(llm, template)

    def create_translation_processor(self, llm, target_language: str) -> Callable[[Chunk], str]:
        """Create a processor for text translation"""
        template = f"""
        Translate the following text to {target_language}:

        {{content}}

        Translation:"""

        return self.create_llm_processor(llm, template)

    def process_with_retry(self,
                          chunks: List[Chunk],
                          processor_func: Callable[[Chunk], Any],
                          max_retries: int = 2,
                          retry_delay: float = 1.0) -> ChunkProcessingResult:
        """
        Process chunks with retry logic for failed chunks

        Args:
            chunks: List of chunks to process
            processor_func: Function to process each chunk
            max_retries: Maximum number of retries for failed chunks
            retry_delay: Delay between retries in seconds

        Returns:
            ChunkProcessingResult with processing results
        """
        logger.info(f"🔄 Processing {len(chunks)} chunks with retry (max_retries={max_retries})")

        # Initial processing
        result = self.process_chunks_parallel(chunks, processor_func)

        # Retry failed chunks
        for retry_attempt in range(max_retries):
            failed_chunks = [
                pc.original_chunk
                for pc in result.processed_chunks
                if not pc.success
            ]

            if not failed_chunks:
                break

            logger.info(f"🔁 Retry attempt {retry_attempt + 1}/{max_retries} for {len(failed_chunks)} failed chunks")

            # Wait before retry
            if retry_delay > 0:
                import time
                time.sleep(retry_delay)

            # Retry failed chunks
            retry_result = self.process_chunks_parallel(failed_chunks, processor_func)

            # Update results
            retry_dict = {pc.original_chunk.id: pc for pc in retry_result.processed_chunks}

            for i, pc in enumerate(result.processed_chunks):
                if not pc.success and pc.original_chunk.id in retry_dict:
                    result.processed_chunks[i] = retry_dict[pc.original_chunk.id]

            # Update counts
            result.successful_count = sum(1 for pc in result.processed_chunks if pc.success)
            result.failed_count = sum(1 for pc in result.processed_chunks if not pc.success)

        logger.success(f"✅ Processing with retry completed: {result.successful_count}/{len(chunks)} successful")
        return result

import time