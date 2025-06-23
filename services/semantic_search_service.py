import fitz  # PyMuPDF
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

class SemanticSearchService:
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.text_chunks = []
        self.chunk_to_file_map = {}

    def _extract_text_from_pdf(self, pdf_path):
        """Extracts text from a PDF file, page by page."""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def _split_text_into_chunks(self, text, chunk_size=1000, chunk_overlap=200):
        """Splits text into overlapping chunks."""
        if not text:
            return []
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - chunk_overlap
        return chunks

    def create_index_from_files(self, file_paths):
        """Creates a FAISS index from a list of file paths."""
        print(f"Creating index from files: {file_paths}")
        all_chunks = []
        
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            if file_path.lower().endswith('.pdf'):
                text = self._extract_text_from_pdf(file_path)
            else: # Assuming other files are plain text
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                except Exception as e:
                    print(f"Error reading text file {file_path}: {e}")
                    continue

            chunks = self._split_text_into_chunks(text)
            for chunk in chunks:
                all_chunks.append(chunk)
                self.chunk_to_file_map[len(self.text_chunks) + len(all_chunks) - 1] = filename

        self.text_chunks = all_chunks
        if not self.text_chunks:
            print("No text chunks to index.")
            self.index = None
            return

        print(f"Encoding {len(self.text_chunks)} text chunks...")
        embeddings = self.model.encode(self.text_chunks, convert_to_tensor=False, show_progress_bar=True)
        
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        print(f"Index created successfully with {self.index.ntotal} vectors.")

    def search(self, query, top_k=5):
        """Searches the index for the most relevant text chunks."""
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1: # FAISS returns -1 for no result
                results.append({
                    'content': self.text_chunks[idx],
                    'file': self.chunk_to_file_map.get(idx, 'Unknown'),
                    'score': distances[0][i]
                })
        
        return results
