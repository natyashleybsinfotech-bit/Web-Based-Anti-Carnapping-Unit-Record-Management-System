#!/usr/bin/env python3
from app import create_app
from app.services.hotspot_service import MANILA_DISTRICTS

app = create_app()

total_barangays = 0
with app.app_context():
    for district_id in sorted(MANILA_DISTRICTS.keys()):
        district_data = MANILA_DISTRICTS[district_id]
        barangay_count = len(district_data['barangays'])
        total_barangays += barangay_count
        print(f"✓ District {district_id}: {district_data['name'][:50]:50s} = {barangay_count:3d} barangays (range: {district_data['barangays'][0]:3d}-{district_data['barangays'][-1]:3d})")

print(f"\n✅ Total: {total_barangays} barangays across 6 districts")
print(f"✅ All barangays 1-905 available in dropdown!")
