"""
FAISS retriever initialization and management
"""
import json
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from data.data_embedding import SentenceTransformerEmbeddings
from src.config.settings import FAISS_INDEX_DIR, FAISS_STATS_PATH, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_DOCUMENTS


def prepare_retriever(pdf_path: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
    """
    Prepare or load FAISS retriever
    
    Args:
        pdf_path: Path to PDF (kept for compatibility)
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        
    Returns:
        tuple: (retriever, total_pdf_pages, total_chunks, supplemental_sources_count)
    """
    embeddings = SentenceTransformerEmbeddings()
    total_pdf_pages = 0
    supplemental_sources_count = 0
    total_chunks = 0

    # Try to load existing index
    if FAISS_INDEX_DIR.exists() and any(FAISS_INDEX_DIR.glob("*")):
        try:
            vector_store = FAISS.load_local(
                str(FAISS_INDEX_DIR),
                embeddings,
                allow_dangerous_deserialization=True,
            )
            print(f"[DEBUG] Loaded FAISS index from {FAISS_INDEX_DIR}")
            
            if FAISS_STATS_PATH.exists():
                stats = json.loads(FAISS_STATS_PATH.read_text(encoding="utf-8"))
                total_pdf_pages = stats.get("pdf_pages", 0)
                total_chunks = stats.get("chunks", 0)
                supplemental_sources_count = stats.get("supplemental_sources", 0)
                print(f"[DEBUG] Index stats: {stats}")
        except Exception as e:
            print(f"[ERROR] Failed to load FAISS index: {e}")
            import traceback
            traceback.print_exc()
            raise
    else:
        # Create new index
        base_documents, prechunked_documents, total_pdf_pages, supplemental_sources_count = collect_labour_documents()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunks = splitter.split_documents(base_documents)
        chunks.extend(prechunked_documents)
        total_chunks = len(chunks)
        
        vector_store = FAISS.from_documents(chunks, embeddings)
        FAISS_INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(FAISS_INDEX_DIR))
        
        stats = {
            "pdf_pages": total_pdf_pages,
            "chunks": total_chunks,
            "supplemental_sources": supplemental_sources_count,
        }
        FAISS_STATS_PATH.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K_DOCUMENTS})
    
    # Test retriever
    print("[DEBUG] Testing retriever with multiple queries...")
    test_queries = ["قانون العمل", "العامل", "المادة 1", "تعريف"]
    test_success = False
    
    for test_q in test_queries:
        try:
            test_docs = retriever.invoke(test_q)
            if test_docs and len(test_docs) > 0:
                print(f"[SUCCESS] Retriever test '{test_q}': Retrieved {len(test_docs)} docs")
                print(f"[DEBUG] Sample doc source: {test_docs[0].metadata.get('source', 'unknown')}")
                print(f"[DEBUG] Sample doc preview: {test_docs[0].page_content[:150]}...")
                test_success = True
                break
        except Exception as e:
            print(f"[WARNING] Retriever test '{test_q}' failed: {e}")
            continue
    
    if not test_success:
        print("[ERROR] Retriever failed all test queries! This is a critical issue.")
        print("[ERROR] The vector store might be empty or corrupted.")
    
    return retriever, total_pdf_pages, total_chunks, supplemental_sources_count
