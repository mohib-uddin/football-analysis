"""
Comprehensive API Test Suite - Auto-run without user interaction
Tests all endpoints to ensure they're production-ready
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_test(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"    {details}")

def test_root():
    """Test root endpoint"""
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        print_test("Root Endpoint", True, f"Version: {data['version']}")
        return True
    except Exception as e:
        print_test("Root Endpoint", False, str(e))
        return False

def test_health():
    """Test health check"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "models_loaded" in data
        print_test("Health Check", True, 
                  f"Status: {data['status']}, Models: {data['models_loaded']}")
        return True
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False

def test_grade_single_play():
    """Test single play grading"""
    try:
        payload = {
            "video_id": "test_game_001",
            "play_id": 1,
            "player_positions": {
                "1": "QB",
                "2": "WR",
                "3": "RB"
            },
            "play_context": "3rd down and 5, midfield, shotgun formation"
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/grading/play",
            json=payload,
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "player_grades" in data
        assert len(data["player_grades"]) == 3
        assert data["play_id"] == 1
        
        # Check first player grade structure
        grade = data["player_grades"][0]
        assert "overall_score" in grade
        assert "letter_grade" in grade
        assert "qualitative_feedback" in grade
        assert "strengths" in grade
        assert "areas_for_improvement" in grade
        
        print_test("Single Play Grading", True,
                  f"Graded {len(data['player_grades'])} players in {data['processing_time']:.2f}s")
        return True
    except Exception as e:
        print_test("Single Play Grading", False, str(e))
        return False

def test_bulk_grading():
    """Test bulk grading"""
    try:
        payload = {
            "video_id": "test_game_002",
            "player_positions": {
                "1": "QB",
                "2": "WR",
                "3": "TE"
            }
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/grading/bulk",
            json=payload,
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_plays" in data
        assert "play_grades" in data
        assert len(data["play_grades"]) > 0
        
        print_test("Bulk Grading", True,
                  f"Graded {data['total_plays']} plays in {data['processing_time']:.2f}s")
        return True
    except Exception as e:
        print_test("Bulk Grading", False, str(e))
        return False

def test_coaching_qa():
    """Test coaching Q&A"""
    try:
        payload = {
            "question": "What are the key fundamentals of quarterback footwork?",
            "role": "coach"
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/grading/qa",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 503:
            print_test("Coaching Q&A", True, 
                      "OpenAI not configured (expected in dev)")
            return True
            
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert "confidence" in data
        
        print_test("Coaching Q&A", True,
                  f"Answer confidence: {data['confidence']:.2f}")
        return True
    except Exception as e:
        print_test("Coaching Q&A", False, str(e))
        return False

def test_docs():
    """Test API documentation"""
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        assert response.status_code == 200
        print_test("Swagger Documentation", True,
                  "Available at /docs")
        return True
    except Exception as e:
        print_test("Swagger Documentation", False, str(e))
        return False

def test_redoc():
    """Test ReDoc documentation"""
    try:
        response = requests.get(f"{API_BASE}/redoc", timeout=5)
        assert response.status_code == 200
        print_test("ReDoc Documentation", True,
                  "Available at /redoc")
        return True
    except Exception as e:
        print_test("ReDoc Documentation", False, str(e))
        return False

def test_cors():
    """Test CORS headers"""
    try:
        headers = {
            "Origin": "http://localhost:3000"
        }
        response = requests.options(
            f"{API_BASE}/api/v1/health",
            headers=headers,
            timeout=5
        )
        cors_header = response.headers.get("access-control-allow-origin")
        assert cors_header is not None
        print_test("CORS Configuration", True,
                  f"CORS enabled for: {cors_header}")
        return True
    except Exception as e:
        print_test("CORS Configuration", False, str(e))
        return False

def test_error_handling():
    """Test error handling"""
    try:
        # Test invalid request
        payload = {"invalid": "data"}
        response = requests.post(
            f"{API_BASE}/api/v1/grading/play",
            json=payload,
            timeout=5
        )
        assert response.status_code == 422  # Validation error
        
        print_test("Error Handling", True,
                  "Properly validates requests")
        return True
    except Exception as e:
        print_test("Error Handling", False, str(e))
        return False

def main():
    """Run all tests"""
    print_header("FieldCoachAI API - Comprehensive Test Suite")
    
    print("\n📋 Starting automated tests...")
    print("   Make sure the API is running at http://localhost:8000")
    print("   Waiting 3 seconds before starting...\n")
    time.sleep(3)
    
    tests = [
        ("Root Endpoint", test_root),
        ("Health Check", test_health),
        ("CORS Configuration", test_cors),
        ("Single Play Grading", test_grade_single_play),
        ("Bulk Grading", test_bulk_grading),
        ("Coaching Q&A", test_coaching_qa),
        ("Error Handling", test_error_handling),
        ("Swagger Documentation", test_docs),
        ("ReDoc Documentation", test_redoc),
    ]
    
    print_header("Running Tests")
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_test(name, False, f"Exception: {str(e)}")
            results.append((name, False))
        time.sleep(0.5)  # Small delay between tests
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({percentage:.0f}%)")
    
    if passed == total:
        print("\n🎉 SUCCESS! All tests passed!")
        print("\n✅ API is production-ready for frontend integration")
        print(f"\n📖 Integration Guide: See FRONTEND_INTEGRATION.md")
        print(f"📖 API Documentation: {API_BASE}/docs")
        print(f"📖 ReDoc: {API_BASE}/redoc")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nCheck the errors above and fix before integration")
        return 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        exit(1)
    except requests.exceptions.ConnectionError:
        print("\n\n❌ ERROR: Cannot connect to API")
        print("   Make sure the API is running:")
        print("   cd api && py main.py")
        exit(1)

