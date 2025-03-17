"""
Vector store implementation using ChromaDB for storing and retrieving problem-solution pairs.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from smolagents import tool

from src.config.settings import settings
from src.utils.logging import logger


class VectorStore:
    """Vector store for managing problem-solution pairs using ChromaDB."""
    
    def __init__(
        self,
        collection_name: str = "k8s_problems",
        embedding_model: Optional[str] = None,
        persist_dir: Optional[str] = None
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            embedding_model: Name of the sentence transformer model to use
            persist_dir: Directory for ChromaDB persistence
        """
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.persist_dir = persist_dir or str(settings.chroma_persist_dir)
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(
                    allow_reset=True,
                    is_persistent=True
                )
            )
            
            # Set up sentence transformer for embeddings
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model_name
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(
                f"Successfully initialized ChromaDB with collection '{collection_name}'"
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise
    
    def add_problem(
        self,
        problem_description: str,
        solution: str,
        metadata: Optional[Dict[str, Any]] = None,
        id_prefix: str = "problem"
    ) -> str:
        """
        Add a problem-solution pair to the vector store.
        
        Args:
            problem_description: Description of the problem
            solution: Solution to the problem
            metadata: Additional metadata about the problem
            id_prefix: Prefix for the generated ID
            
        Returns:
            str: ID of the added problem
        """
        try:
            # Generate a unique ID
            count = len(self.collection.get()["ids"]) if self.collection.count() > 0 else 0
            problem_id = f"{id_prefix}_{count + 1}"
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            metadata["solution"] = solution
            
            # Add to collection
            self.collection.add(
                documents=[problem_description],
                metadatas=[metadata],
                ids=[problem_id]
            )
            
            logger.info(f"Added problem-solution pair with ID: {problem_id}")
            return problem_id
        
        except Exception as e:
            logger.error(f"Error adding problem to vector store: {str(e)}")
            raise
    
    def find_similar_problems(
        self,
        query: str,
        n_results: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find similar problems in the vector store.
        
        Args:
            query: Problem description to search for
            n_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1) for results
            
        Returns:
            List of similar problems with their solutions and metadata
        """
        try:
            if self.collection.count() == 0:
                return []
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["metadatas", "documents", "distances"]
            )
            
            # Process results
            similar_problems = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # Convert distance to similarity score (cosine distance to similarity)
                similarity = 1 - (distance / 2)
                
                if similarity >= similarity_threshold:
                    similar_problems.append({
                        "problem": doc,
                        "solution": metadata.pop("solution"),  # Extract solution from metadata
                        "similarity": similarity,
                        "metadata": metadata
                    })
            
            return similar_problems
        
        except Exception as e:
            logger.error(f"Error searching for similar problems: {str(e)}")
            raise
    
    def get_all_problems(self) -> List[Dict[str, Any]]:
        """Get all problems and their solutions from the vector store."""
        try:
            if self.collection.count() == 0:
                return []
            
            results = self.collection.get(include=["metadatas", "documents"])
            
            return [
                {
                    "id": id_,
                    "problem": doc,
                    "solution": metadata.pop("solution"),
                    "metadata": metadata
                }
                for id_, doc, metadata in zip(
                    results["ids"],
                    results["documents"],
                    results["metadatas"]
                )
            ]
        
        except Exception as e:
            logger.error(f"Error getting all problems: {str(e)}")
            raise
    
    def delete_problem(self, problem_id: str):
        """Delete a problem-solution pair by ID."""
        try:
            self.collection.delete(ids=[problem_id])
            logger.info(f"Deleted problem with ID: {problem_id}")
        except Exception as e:
            logger.error(f"Error deleting problem {problem_id}: {str(e)}")
            raise
    
    def clear_all(self):
        """Delete all problems from the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Cleared all problems from the vector store")
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise


# Create a global vector store instance
vector_store = VectorStore()


# SmolAgents tools for vector store operations
@tool
def add_problem(
    problem_description: str,
    solution: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Add a problem-solution pair to the vector store.
    
    Args:
        problem_description: Description of the problem
        solution: Solution to the problem
        metadata: Additional metadata about the problem
    """
    try:
        problem_id = vector_store.add_problem(problem_description, solution, metadata)
        return f"Successfully added problem with ID: {problem_id}"
    except Exception as e:
        return f"Error adding problem: {str(e)}"


@tool
def find_similar_problems(
    query: str,
    n_results: int = 3,
    similarity_threshold: float = 0.7
) -> str:
    """
    Find similar problems in the vector store.
    
    Args:
        query: Problem description to search for
        n_results: Maximum number of results to return
        similarity_threshold: Minimum similarity score (0-1) for results
    """
    try:
        similar_problems = vector_store.find_similar_problems(
            query, n_results, similarity_threshold
        )
        
        if not similar_problems:
            return "No similar problems found."
        
        result = "Found similar problems:\n\n"
        for i, problem in enumerate(similar_problems, 1):
            result += f"Problem {i} (Similarity: {problem['similarity']:.2f}):\n"
            result += f"Description: {problem['problem']}\n"
            result += f"Solution: {problem['solution']}\n\n"
        
        return result
    except Exception as e:
        return f"Error finding similar problems: {str(e)}"


@tool
def get_all_problems() -> str:
    """Get all problems and their solutions from the vector store."""
    try:
        problems = vector_store.get_all_problems()
        
        if not problems:
            return "No problems found in the vector store."
        
        result = f"Found {len(problems)} problems:\n\n"
        for i, problem in enumerate(problems, 1):
            result += f"Problem {i} (ID: {problem['id']}):\n"
            result += f"Description: {problem['problem']}\n"
            result += f"Solution: {problem['solution']}\n\n"
        
        return result
    except Exception as e:
        return f"Error getting all problems: {str(e)}"


# List of all vector store tools for easy import
vector_store_tools = [
    add_problem,
    find_similar_problems,
    get_all_problems
] 