#Interverted Indexer class for recall engine. This class will be responsible for building the index and retrieving documents based on the index.
import os
import pickle
from recall_engine.cli.misc import CACHE_PATH, dataset_loader_json
from recall_engine.search_engine.tokenizer import Tokenizer


class Indexer:
    """Inverted index for efficient document retrieval by terms.
    
    Attributes:
        index: Maps terms to lists of document IDs containing them.
        doc_map: Maps document IDs to their full document data.
        default_file_path: Default path for saving/loading the index.
    """
    def __init__(self, document_index: dict[str, list[str]] = {}, document_map: dict[str,dict[str,str]] = {}, filePath: str = CACHE_PATH) -> None:
        self.index = document_index
        self.doc_map = document_map
        self.default_file_path = filePath
        self.tokenizer = Tokenizer()
        
        
    def get_index(self) -> dict[str, list[str]]:
        """Returns the current inverted index."""
        return self.index
    
    def get_doc_map(self) -> dict[str, dict[str,str]]:
        """Returns the current document map."""
        return self.doc_map
        
    def __add_document(self, doc_id: str, text: str) -> None:
        """Add a document to the index by tokenizing text and updating term mappings.
        
        Args:
            doc_id: Unique document identifier.
            text: Text content to index.
        """
        
        # Tokenize text and add each token to the index
        tokens = self.tokenizer.tokenize(text)
        for token in tokens:
            if token not in self.index:
                self.index[token] = []
            if doc_id not in self.index[token]:
                self.index[token].append(doc_id)
    def build(self, docPath: str, dataKey:str = "",docIdKey: str = "id", excludeDocKeys: list[str] = ["id"]) -> None:
        """Build the inverted index from a JSON file.
        
        Args:
            docPath: Path to JSON file containing documents.
            dataKey: Key to extract specific data from each document (optional).
            docIdKey: Document field to use as unique ID.
            excludeDocKeys: Fields to exclude from indexing.
        """
        try:
            data = dataset_loader_json(docPath)
            documents: list[dict[str,str]] = data if dataKey == "" else data[str(dataKey)] #type: ignore
            for doc in documents:
                doc_id = str(doc[docIdKey])
                # Combine all text fields except the excluded keys into a single string for indexing
                text_content = " "
                for key, value in doc.items():
                    if key not in excludeDocKeys:
                        text_content += str(value) + " "
                self.doc_map[doc_id] = doc
                self.__add_document(doc_id, text_content.strip())
        except Exception as e:
            print(f"Error Building Index: {e}", flush=True)
            exit()
            
            
    def save(self, filepath: str = "") -> None:
        """Save index and document map to disk.
        
        Args:
            filepath: Optional file path; defaults to self.default_file_path if not provided.
        """
        if filepath == "":
            filepath = self.default_file_path
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as file:
            pickle.dump({"index": self.index, "doc_map": self.doc_map}, file)
            
    def load(self, filepath: str = "", force: bool = False) -> None:
        """Load index and document map from disk.
        
        Args:
            filepath: Optional file path; defaults to self.default_file_path if not provided.
            force: If True, force reload even if index and doc_map are already populated.
        
        Raises:
            RuntimeError: If index already populated and force=False.
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is corrupted or doesn't contain expected keys.
        """
        if self.doc_map and self.index and not force:
            raise RuntimeError("Index and document map are already populated. Use force=True to reload.")
        
        if filepath == "":
            filepath = self.default_file_path
        
        try:
            with open(filepath, "rb") as file:
                data = pickle.load(file)
                self.index = data["index"]
                self.doc_map = data["doc_map"]
        except FileNotFoundError:
            raise FileNotFoundError(f"Index file not found at {filepath}")
        except pickle.UnpicklingError as e:
            raise ValueError(f"Failed to load index: corrupted file. {str(e)}")
        except KeyError as e:
            raise ValueError(f"Invalid index file: missing key {str(e)}")
    
    def load_or_build(self, docPath: str, dataKey: str = "", docIdKey: str = "id", excludeDocKeys: list[str] = ["id"]) -> None:
        """Load index from disk or build it if loading fails.
        
        Args:
            docPath: Path to JSON file containing documents (used for building if loading fails).
            dataKey: Key to extract documents from JSON (used for building).
            docIdKey: Document field to use as unique ID (used for building).
            excludeDocKeys: Fields to exclude from indexing (used for building).
        """
        try:
            self.load()
        except (FileNotFoundError, ValueError) as e:
            print(f"Loading index failed: {str(e)}. Building new index.")
            self.build(docPath, dataKey=dataKey, docIdKey=docIdKey, excludeDocKeys=excludeDocKeys)
            self.save()
    
    def get_documents(self, terms: list[str], operation: str = "") -> list[dict[str,str]]:
        """Retrieve documents containing a given term.
        
        Args:
            terms: The terms to search for in the index.
            operation: The boolean operation to apply ("AND" or "OR" or "NOT").
        
        Returns:
            A list of document data dictionaries that contain the term.
        """
        tokenized_term = [token for term in terms for token in self.tokenizer.tokenize(term)]
        doc_ids: list[str] = []
        for token in tokenized_term:
            if token in self.index:
                for doc_id in self.index[token]:
                    doc_ids.append(doc_id)

        return [self.doc_map[doc_id] for doc_id in set(doc_ids)]