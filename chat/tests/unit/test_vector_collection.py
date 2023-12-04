from django.test import TestCase
import vcr
from chat.ai.vector_collection import Document, VectorCollection

class TestDocument(TestCase):
    def test_to_embed_str(self):
        doc = Document("1", {"text": "Hello, world!"})
        self.assertEqual(doc.to_embed_str(), '{"text": "Hello, world!"}')

    def test_id_conversion(self):
        doc = Document(123, {"text": "Hello, world!"})
        self.assertEqual(doc.id, "123")  # Check that the id is converted to a string

    def test_data_assignment(self):
        data = {"text": "Hello, world!"}
        doc = Document("1", data)
        self.assertEqual(doc.data, data)  # Check that the data is correctly assigned

class TestVectorCollection(TestCase):
    def setUp(self):
        self.collection = VectorCollection(collection_name="test")

    @vcr.use_cassette('chat/test/fixtures/vcr_cassettes/vector_collection.yaml', filter_headers=[('authorization', None)])
    def test_add_and_search(self):
        doc1 = Document("1", {"text": "Hello, world!"})
        doc2 = Document("2", {"text": "Goodbye, world!"})

        self.collection.add(doc1)
        self.collection.add(doc2)

        results = self.collection.search("world", n_results=2)
        length = len(results)

        # Check that the search results contain the correct documents
        self.assertEqual(length, 2)
        self.assertIn(doc1.data, results)
        self.assertIn(doc2.data, results)

    def test_get_chroma_collection(self):
        # Check that the collection has the correct name
        self.assertEqual(self.collection.collection.name, "test")

    def test_to_embed_str(self):
        doc = Document("1", {"text": "Hello, world!"})
        self.assertEqual(doc.to_embed_str(), '{"text": "Hello, world!"}')