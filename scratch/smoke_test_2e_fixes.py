import os
import sys
import json
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import SessionLocal
from models import JobApplicationAsset

client = TestClient(app)

def test_download_endpoint():
    db = SessionLocal()
    
    # 1. Fetch invalid asset download
    print("1. Fetching invalid asset download...")
    res = client.get("/job-monitoring/assets/999999/download")
    print("Status:", res.status_code)
    print("Body:", res.json())
    assert res.status_code == 404, "Invalid asset should return 404"

    # 2. Find a valid asset in DB and verify download
    asset = db.query(JobApplicationAsset).first()
    if asset:
        print(f"\n2. Fetching valid asset ID={asset.id} download...")
        res = client.get(f"/job-monitoring/assets/{asset.id}/download")
        print("Status:", res.status_code)
        print("Body:", res.text)
        print("Content length:", len(res.content))
        assert res.status_code == 200, "Valid asset download should return 200"
        
        # 3. Test path traversal injection
        # Let's temporarily modify the asset file_path in DB to point outside generated_assets/
        original_path = asset.file_path
        print(f"\n3. Testing path traversal protection for asset ID={asset.id}...")
        
        try:
            # Pointing path outside generated_assets
            asset.file_path = "/etc/passwd"
            db.commit()
            
            res_injection = client.get(f"/job-monitoring/assets/{asset.id}/download")
            print("Status:", res_injection.status_code)
            print("Body:", res_injection.json())
            assert res_injection.status_code == 403, "Access to file outside generated_assets should be forbidden (403)"
            print("Path traversal blocked successfully!")
        finally:
            # Restore original path
            asset.file_path = original_path
            db.commit()
            
    else:
        print("No assets found in database to test valid download.")

    print("\nAll Phase 2E backend UI fixes smoke tests passed successfully!")
    db.close()

if __name__ == "__main__":
    test_download_endpoint()
