"""
Test script for FieldCoachAI API
Tests all endpoints to ensure they're working correctly
"""
import requests
import json
import sys

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/v1/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check: {data['status']}")
        print(f"   Models loaded: {data['models_loaded']}")
        print(f"   Version: {data['version']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root():
    """Test root endpoint"""
    print("\n🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{API_BASE}/")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Root endpoint: {data['message']}")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_grading_single_play():
    """Test single play grading"""
    print("\n🔍 Testing single play grading...")
    try:
        payload = {
            "video_id": "test_video_001",
            "play_id": 1,
            "player_positions": {
                "1": "QB",
                "2": "WR",
                "3": "RB",
                "4": "OL",
                "5": "DL"
            },
            "play_context": "3rd and 5, midfield, shotgun formation"
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/grading/play",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Graded play #{data['play_id']} in video '{data['video_id']}'")
        print(f"   Player grades: {len(data['player_grades'])}")
        print(f"   Processing time: {data['processing_time']:.2f}s")
        
        # Show first player grade
        if data['player_grades']:
            grade = data['player_grades'][0]
            print(f"\n   Sample Grade - Player #{grade['player_id']} ({grade['position']}):")
            print(f"   Overall: {grade['letter_grade']} ({grade['overall_score']}/100)")
            print(f"   Feedback: {grade['qualitative_feedback'][:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Single play grading failed: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return False

def test_bulk_grading():
    """Test bulk grading"""
    print("\n🔍 Testing bulk grading...")
    try:
        payload = {
            "video_id": "test_video_002",
            "player_positions": {
                "1": "QB",
                "2": "WR",
                "3": "TE",
                "4": "RB"
            }
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/grading/bulk",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Bulk grading completed")
        print(f"   Total plays: {data['total_plays']}")
        print(f"   Total processing time: {data['processing_time']:.2f}s")
        
        return True
    except Exception as e:
        print(f"❌ Bulk grading failed: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return False

def test_coaching_qa():
    """Test coaching Q&A"""
    print("\n🔍 Testing coaching Q&A...")
    try:
        payload = {
            "question": "How can I improve my quarterback's decision-making under pressure?",
            "role": "coach"
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/grading/qa",
            json=payload
        )
        
        if response.status_code == 503:
            print("⚠️  OpenAI not configured - skipping Q&A test")
            print("   Set OPENAI_API_KEY in .env to enable this feature")
            return True
        
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Coaching Q&A response received")
        print(f"   Question: {data['question'][:60]}...")
        print(f"   Answer: {data['answer'][:100]}...")
        print(f"   Confidence: {data['confidence']:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Coaching Q&A failed: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return False

def test_docs():
    """Test Swagger docs availability"""
    print("\n🔍 Testing API documentation...")
    try:
        response = requests.get(f"{API_BASE}/docs")
        response.raise_for_status()
        print(f"✅ Swagger docs available at {API_BASE}/docs")
        return True
    except Exception as e:
        print(f"❌ Swagger docs failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 FieldCoachAI API Test Suite")
    print("=" * 60)
    
    print("\nMake sure the API is running:")
    print("  cd api && python main.py")
    print("\nor:")
    print("  uvicorn api.main:app --reload")
    
    input("\nPress Enter to start testing...")
    
    tests = [
        ("Root Endpoint", test_root),
        ("Health Check", test_health),
        ("Single Play Grading", test_grading_single_play),
        ("Bulk Grading", test_bulk_grading),
        ("Coaching Q&A", test_coaching_qa),
        ("API Documentation", test_docs),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! API is working correctly.")
        print(f"\n📖 View API docs at: {API_BASE}/docs")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

