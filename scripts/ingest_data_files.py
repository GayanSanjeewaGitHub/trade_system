"""
Script to manually ingest data files into the RAG system.
Run this after starting the backend to load default documents.
"""

import requests
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"
INGEST_ENDPOINT = f"{API_BASE_URL}/ingest"

def ingest_file(file_path: Path, document_type: str):
    """Ingest a single file."""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/plain')}
            data = {'document_type': document_type}
            
            print(f"Ingesting {file_path.name}...")
            response = requests.post(INGEST_ENDPOINT, files=files, data=data, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS: {file_path.name}")
                print(f"   Chunks created: {result.get('chunks_created', 0)}")
                return True
            else:
                print(f"❌ FAILED: {file_path.name}")
                print(f"   Status code: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ ERROR: {file_path.name}")
        print(f"   {str(e)}")
        return False

def main():
    """Main function to ingest all data files."""
    print("=" * 60)
    print("Document Ingestion Script")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend is not healthy. Please start the backend first.")
            print("   Run: docker-compose -f docker/docker-compose.yml up")
            return
        print("✅ Backend is running\n")
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to backend. Please start the backend first.")
        print("   Run: docker-compose -f docker/docker-compose.yml up")
        return
    
    # Define files to ingest
    data_dir = Path("src/data")
    
    files_to_ingest = [
        (data_dir / "faq.txt", "faq"),
        (data_dir / "policies.txt", "policy"),
        (data_dir / "product_info.txt", "product_info"),
    ]
    
    # Ingest each file
    success_count = 0
    failed_count = 0
    
    print("Starting ingestion...\n")
    
    for file_path, doc_type in files_to_ingest:
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            failed_count += 1
            continue
        
        if ingest_file(file_path, doc_type):
            success_count += 1
        else:
            failed_count += 1
        print()
    
    # Summary
    print("=" * 60)
    print("Ingestion Summary")
    print("=" * 60)
    print(f"✅ Successfully ingested: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total: {success_count + failed_count}")
    print()
    
    if success_count > 0:
        print("🎉 Documents are now available in the chatbot!")
        print("   Try asking: 'What are your trading policies?'")
    
    if failed_count > 0:
        print("\n⚠️  Some documents failed to ingest.")
        print("   Check the error messages above for details.")

if __name__ == "__main__":
    main()
