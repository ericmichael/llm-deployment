import os
import json
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from tenacity import retry, wait_exponential, stop_after_attempt
from django.conf import settings

class Document:
    """
    A class to represent a Document.

    ...

    Attributes
    ----------
    id : str
        a unique identifier for the document
    data : dict
        a dictionary containing information about the document

    Methods
    -------
    to_embed_str():
        Converts the data attribute to a string for embedding in the vector database
    """

    def __init__(self, id, data):
        """
        Constructs all the necessary attributes for the Document object.

        Parameters
        ----------
            id : str
                a unique identifier for the document
            data : dict
                a dictionary containing information about the document
        """
        self.id = str(id) if isinstance(id, int) else id
        self.data = data

    def to_embed_str(self):
        """
        Converts the data attribute to a string for embedding in the vector database

        Returns
        -------
        str
            a string representation of the document for embedding in the vector database
        """
        return json.dumps(self.data)


class VectorCollection:
    """
    A class to represent a Vector Collection.

    ...

    Attributes
    ----------
    chroma_client : chromadb.PersistentClient or chromadb.Client
        a client to interact with the ChromaDB
    collection : chromadb.Collection
        a collection of documents in the ChromaDB

    Methods
    -------
    _get_chroma_collection(collection_name):
        Retrieves or creates a collection in the ChromaDB.
    search(query, n_results=10):
        Searches the collection for a query and returns the top n_results.
    add(document):
        Adds a document to the collection.
    """

    def __init__(self, collection_name="default"):
        """
        Constructs all the necessary attributes for the VectorCollection object.

        Parameters
        ----------
            path : str, optional
                the path to the ChromaDB storage. If None, an in-memory client will be used.
            collection_name : str
                the name of the collection in the ChromaDB
        """
        path = settings.CHROMADB_STORAGE_PATH

        # When path is given, create directories if they do not exist and create a PersistentClient
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=path)
        else:
            self.chroma_client = chromadb.Client()
        self.collection = self._get_chroma_collection(collection_name)

    def _get_chroma_collection(self, collection_name):
        """
        Retrieves or creates a collection in the ChromaDB.

        Parameters
        ----------
            collection_name : str
                the name of the collection in the ChromaDB

        Returns
        -------
        chromadb.Collection
            a collection of documents in the ChromaDB
        """
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                        api_key=settings.OPENAI_API_KEY,
                        api_base=settings.OPENAI_API_BASE,
                        model_name="text-embedding-ada-002"
                    )

        collection = self.chroma_client.get_or_create_collection(name=collection_name, embedding_function=openai_ef)
        return collection

    @retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5), reraise=True)
    def search(self, query, n_results=10):
        """
        Searches the collection for a query and returns the top n_results.

        Parameters
        ----------
            query : str
                the query to search for in the collection
            n_results : int, optional
                the number of results to return (default is 10)

        Returns
        -------
        list
            a list of metadata for the top n_results documents
        """
        metadatas = []
        results = self.collection.query(query_texts=[query], n_results=n_results)

        for i in range(len(results['ids'][0])):
            metadatas.append(results["metadatas"][0][i])
            
        return metadatas

    @retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5), reraise=True)
    def add(self, document):
        """
        Adds a document to the collection.

        Parameters
        ----------
            document : Document
                the document to add to the collection
        """
        self.collection.add(
            documents=[document.to_embed_str()],
            metadatas=[document.data],
            ids=[document.id]
        )