"""
Memory module for the AI Assistant.

This module implements a simple memory system to help the AI assistant
remember information across conversations using TF-IDF for text similarity.
"""

import os
import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from colorama import Fore, Style
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
MEMORY_DIR = Path(os.getenv('MEMORY_DIR', 'memory'))
MEMORY_FILE = MEMORY_DIR / "memories.json"

class MemorySystem:
    """Simple memory system for the AI Assistant"""

    def __init__(self):
        """Initialize the memory system"""
        self._ensure_memory_dir()
        self.memories = self._load_memories()
        self.vectorizer = TfidfVectorizer(stop_words='english')

        # Initialize the vectorizer if we have memories
        if self.memories:
            memory_texts = [m['content'] for m in self.memories]
            self.tfidf_matrix = self.vectorizer.fit_transform(memory_texts)
        else:
            self.tfidf_matrix = None

        print(f"{Fore.GREEN}Memory system initialized with {len(self.memories)} memories{Style.RESET_ALL}")

    def _ensure_memory_dir(self):
        """Ensure the memory directory exists"""
        MEMORY_DIR.mkdir(exist_ok=True)

    def _load_memories(self):
        """Load memories from file or return empty list if file doesn't exist"""
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"{Fore.RED}Error loading memories: {e}{Style.RESET_ALL}")
                return []
        return []

    def _save_memories(self):
        """Save memories to file"""
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)

    def add_memory(self, content):
        """
        Add a new memory

        Args:
            content: The memory content to add

        Returns:
            True if memory was added, False if it's too similar to existing memories
        """
        # Clean the content
        content = content.strip()
        if not content:
            return False

        # Check if memory is too similar to existing ones
        if self.memories and self._is_too_similar(content):
            print(f"{Fore.YELLOW}Memory too similar to existing memories, not adding{Style.RESET_ALL}")
            return False

        # Create new memory
        memory = {
            'id': len(self.memories),
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'created_at': time.time()
        }

        # Add to memories list
        self.memories.append(memory)

        # Update the TF-IDF matrix
        if self.tfidf_matrix is None:
            # First memory
            self.tfidf_matrix = self.vectorizer.fit_transform([content])
        else:
            # Add to existing matrix
            self.tfidf_matrix = self.vectorizer.fit_transform([m['content'] for m in self.memories])

        # Save memories
        self._save_memories()

        print(f"{Fore.GREEN}Added new memory: {content[:50]}...{Style.RESET_ALL}")
        return True

    def _is_too_similar(self, content, similarity_threshold=0.85):
        """Check if content is too similar to existing memories"""
        if not self.memories or self.tfidf_matrix is None:
            return False

        # Transform the new content
        try:
            new_tfidf = self.vectorizer.transform([content])

            # Calculate similarity with all existing memories
            similarities = cosine_similarity(new_tfidf, self.tfidf_matrix).flatten()

            # Check if any similarity is above threshold
            return np.max(similarities) > similarity_threshold
        except Exception as e:
            print(f"{Fore.RED}Error checking similarity: {e}{Style.RESET_ALL}")
            return False

    def retrieve_memories(self, query, k=3):
        """
        Retrieve relevant memories based on a query

        Args:
            query: The query to search for
            k: Number of memories to retrieve

        Returns:
            List of relevant memories
        """
        if not self.memories or not query.strip() or self.tfidf_matrix is None:
            return []

        try:
            # Transform the query
            query_tfidf = self.vectorizer.transform([query])

            # Calculate similarity with all memories
            similarities = cosine_similarity(query_tfidf, self.tfidf_matrix).flatten()

            # Get top k similar memories
            top_indices = similarities.argsort()[-k:][::-1]

            # Filter by minimum similarity
            results = []
            for i in top_indices:
                similarity = similarities[i]
                if similarity > 0.1:  # Minimum similarity threshold
                    results.append({
                        'content': self.memories[i]['content'],
                        'similarity': float(similarity),
                        'timestamp': self.memories[i]['timestamp']
                    })

            return results
        except Exception as e:
            print(f"{Fore.RED}Error retrieving memories: {e}{Style.RESET_ALL}")
            return []

    def get_all_memories(self):
        """Get all memories"""
        return self.memories

    def clear_all_memories(self):
        """Clear all memories"""
        self.memories = []
        self.tfidf_matrix = None
        self._save_memories()

        print(f"{Fore.YELLOW}All memories cleared{Style.RESET_ALL}")
        return True

    def format_memories_for_context(self, memories):
        """Format memories for inclusion in context"""
        if not memories:
            return ""

        formatted = "Here are some relevant memories I have:\n\n"
        for i, memory in enumerate(memories):
            formatted += f"{i+1}. {memory['content']}\n"

        return formatted

# Singleton instance
_memory_system = None

def get_memory_system():
    """Get the memory system singleton instance"""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem()
    return _memory_system

def add_memory(content):
    """Add a memory to the system"""
    memory_system = get_memory_system()
    return memory_system.add_memory(content)

def retrieve_memories(query, k=3):
    """Retrieve memories relevant to a query"""
    memory_system = get_memory_system()
    return memory_system.retrieve_memories(query, k)

def get_all_memories():
    """Get all memories"""
    memory_system = get_memory_system()
    return memory_system.get_all_memories()

def clear_all_memories():
    """Clear all memories"""
    memory_system = get_memory_system()
    return memory_system.clear_all_memories()

def format_memories_for_context(memories):
    """Format memories for inclusion in context"""
    memory_system = get_memory_system()
    return memory_system.format_memories_for_context(memories)
