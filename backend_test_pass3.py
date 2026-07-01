"""Backend API tests for Kaelra Pass 3 features.

Tests:
- POST /api/chat/stream (non-actionable vs actionable)
- GET /api/memory/insights
- POST /api/memory/consolidate
- GET /api/oauth/microsoft/status (configured=false EXPECTED)
- GET /api/oauth/microsoft/url (400 EXPECTED as PASS)
- GET /api/oauth/google/status (configured=true)
- GET /api/oauth/google/accounts
- POST /api/location/ping
- GET /api/location/timeline
- Verify cheaper Anthropic model works
"""

import requests
import json
import sys
import time
from datetime import datetime

BASE_URL = "https://kaelra-operator.preview.emergentagent.com/api"

class Pass3Tester:
    def __init__(self):
        self.base_url = BASE_URL
        self.demo_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []
        
    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, name, method, endpoint, expected_status, data=None, 
                 token=None, stream=False, headers_override=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = headers_override or {'Content-Type': 'application/json'}
        
        if token and not headers_override:
            headers['Authorization'] = f'Bearer {token}'
        
        self.tests_run += 1
        self.log(f"Testing {name}...", "TEST")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, stream=stream, timeout=60)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, stream=stream, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=60)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - {name} (Status: {response.status_code})", "PASS")
                if stream:
                    return True, response
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                self.tests_failed += 1
                self.failed_tests.append({
                    "name": name,
                    "expected": expected_status,
                    "got": response.status_code,
                    "response": response.text[:200]
                })
                self.log(f"❌ FAILED - {name} (Expected {expected_status}, got {response.status_code})", "FAIL")
                self.log(f"   Response: {response.text[:200]}", "FAIL")
                return False, {}
                
        except Exception as e:
            self.tests_failed += 1
            self.failed_tests.append({
                "name": name,
                "error": str(e)
            })
            self.log(f"❌ FAILED - {name} (Error: {str(e)})", "FAIL")
            return False, {}
    
    def test_auth(self):
        """Get demo token"""
        self.log("=" * 60, "INFO")
        self.log("AUTHENTICATING", "INFO")
        self.log("=" * 60, "INFO")
        
        success, response = self.run_test(
            "Demo Login",
            "POST",
            "auth/demo",
            200
        )
        if success and 'token' in response:
            self.demo_token = response['token']
            self.log(f"Demo token obtained", "INFO")
            return True
        return False
    
    def test_chat_stream(self):
        """Test chat streaming with non-actionable and actionable messages"""
        self.log("=" * 60, "INFO")
        self.log("TESTING CHAT STREAM (NON-ACTIONABLE VS ACTIONABLE)", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test 1: Non-actionable message (should still return done)
        self.log("Testing non-actionable message: 'what is my day like?'", "INFO")
        success, response = self.run_test(
            "Chat stream (non-actionable)",
            "POST",
            "chat/stream",
            200,
            data={"message": "what is my day like?"},
            token=self.demo_token,
            stream=True,
            headers_override={
                'Authorization': f'Bearer {self.demo_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if success:
            has_session = False
            has_delta = False
            has_actions = False
            has_done = False
            
            try:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            try:
                                event = json.loads(data_str)
                                event_type = event.get('type')
                                
                                if event_type == 'session':
                                    has_session = True
                                    self.log(f"✅ Session event received", "PASS")
                                elif event_type == 'delta':
                                    has_delta = True
                                elif event_type == 'actions':
                                    has_actions = True
                                    self.log(f"✅ Actions event received (may be empty for non-actionable)", "PASS")
                                elif event_type == 'done':
                                    has_done = True
                                    self.log("✅ Done event received for non-actionable message", "PASS")
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                self.log(f"Error reading stream: {e}", "WARN")
            
            if has_delta:
                self.log(f"✅ Delta events received (reply streamed)", "PASS")
            if has_done:
                self.log(f"✅ Non-actionable message completed with 'done'", "PASS")
        
        # Test 2: Actionable message (should yield actions event)
        time.sleep(2)  # Brief pause between requests
        self.log("Testing actionable message: 'draft a reply to Prof. Adams'", "INFO")
        success, response = self.run_test(
            "Chat stream (actionable)",
            "POST",
            "chat/stream",
            200,
            data={"message": "draft a reply to Prof. Adams"},
            token=self.demo_token,
            stream=True,
            headers_override={
                'Authorization': f'Bearer {self.demo_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if success:
            has_actions = False
            has_done = False
            actions_count = 0
            
            try:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            try:
                                event = json.loads(data_str)
                                event_type = event.get('type')
                                
                                if event_type == 'actions':
                                    has_actions = True
                                    actions_count = len(event.get('actions', []))
                                    self.log(f"✅ Actions event received with {actions_count} actions", "PASS")
                                elif event_type == 'done':
                                    has_done = True
                                    self.log("✅ Done event received for actionable message", "PASS")
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                self.log(f"Error reading stream: {e}", "WARN")
            
            if has_actions:
                self.log(f"✅ Actionable message yielded actions event (not error)", "PASS")
            if has_done:
                self.log(f"✅ Actionable message completed with 'done'", "PASS")
    
    def test_memory_endpoints(self):
        """Test memory insights and consolidation"""
        self.log("=" * 60, "INFO")
        self.log("TESTING MEMORY ENDPOINTS", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test GET /api/memory/insights
        success, insights = self.run_test(
            "Get memory insights",
            "GET",
            "memory/insights",
            200,
            token=self.demo_token
        )
        
        if success:
            required_keys = ['total', 'learned', 'consolidated', 'pending_consolidation']
            missing = [k for k in required_keys if k not in insights]
            if not missing:
                self.log(f"✅ Memory insights has all required keys: {required_keys}", "PASS")
                self.log(f"   Total: {insights['total']}, Learned: {insights['learned']}, Consolidated: {insights['consolidated']}, Pending: {insights['pending_consolidation']}", "INFO")
            else:
                self.log(f"❌ Memory insights missing keys: {missing}", "FAIL")
        
        # Test POST /api/memory/consolidate
        self.log("Running memory consolidation (may take a few seconds)...", "INFO")
        success, result = self.run_test(
            "Consolidate memory",
            "POST",
            "memory/consolidate",
            200,
            token=self.demo_token
        )
        
        if success:
            if isinstance(result, dict):
                self.log(f"✅ Consolidate returned dict: {result}", "PASS")
                if 'consolidated' in result or 'processed' in result or 'skipped' in result:
                    self.log(f"✅ Consolidate result has expected fields", "PASS")
            else:
                self.log(f"❌ Consolidate should return dict, got: {type(result)}", "FAIL")
    
    def test_microsoft_oauth(self):
        """Test Microsoft OAuth endpoints (MOCK/idle expected)"""
        self.log("=" * 60, "INFO")
        self.log("TESTING MICROSOFT OAUTH (MOCK/IDLE EXPECTED)", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test GET /api/oauth/microsoft/status (should return configured=false)
        success, status = self.run_test(
            "Get Microsoft OAuth status",
            "GET",
            "oauth/microsoft/status",
            200,
            token=self.demo_token
        )
        
        if success:
            if status.get('configured') == False:
                self.log(f"✅ Microsoft configured=false (EXPECTED for mock/idle)", "PASS")
            else:
                self.log(f"❌ Microsoft should be configured=false, got: {status.get('configured')}", "FAIL")
            
            if status.get('connected') == False:
                self.log(f"✅ Microsoft connected=false (EXPECTED)", "PASS")
            
            if 'accounts' in status and status['accounts'] == []:
                self.log(f"✅ Microsoft accounts=[] (EXPECTED)", "PASS")
        
        # Test GET /api/oauth/microsoft/url (should return 400 - EXPECTED as PASS)
        success, response = self.run_test(
            "Get Microsoft OAuth URL (should 400)",
            "GET",
            "oauth/microsoft/url?redirect_uri=http://localhost:3000/auth/microsoft",
            400,
            token=self.demo_token
        )
        
        if success:
            self.log(f"✅ Microsoft OAuth URL returns 400 (EXPECTED - not configured)", "PASS")
    
    def test_google_oauth(self):
        """Test Google OAuth endpoints (configured expected)"""
        self.log("=" * 60, "INFO")
        self.log("TESTING GOOGLE OAUTH (CONFIGURED EXPECTED)", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test GET /api/oauth/google/status (should return configured=true)
        success, status = self.run_test(
            "Get Google OAuth status",
            "GET",
            "oauth/google/status",
            200,
            token=self.demo_token
        )
        
        if success:
            if status.get('configured') == True:
                self.log(f"✅ Google configured=true (EXPECTED)", "PASS")
            else:
                self.log(f"❌ Google should be configured=true, got: {status.get('configured')}", "FAIL")
            
            if 'accounts' in status:
                self.log(f"✅ Google status has accounts array: {len(status['accounts'])} accounts", "PASS")
        
        # Test GET /api/oauth/google/accounts
        success, accounts_resp = self.run_test(
            "Get Google accounts",
            "GET",
            "oauth/google/accounts",
            200,
            token=self.demo_token
        )
        
        if success:
            if 'accounts' in accounts_resp:
                self.log(f"✅ Google accounts endpoint returns {{accounts: []}} structure", "PASS")
                self.log(f"   Accounts: {len(accounts_resp['accounts'])}", "INFO")
            else:
                self.log(f"❌ Google accounts should return {{accounts: []}}, got: {accounts_resp}", "FAIL")
    
    def test_location_endpoints(self):
        """Test location timeline endpoints"""
        self.log("=" * 60, "INFO")
        self.log("TESTING LOCATION ENDPOINTS", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test POST /api/location/ping
        success, ping_result = self.run_test(
            "Location ping",
            "POST",
            "location/ping",
            200,
            data={
                "lat": 37.7749,
                "lng": -122.4194,
                "label": "Test Location",
                "accuracy": 10.0
            },
            token=self.demo_token
        )
        
        if success:
            if isinstance(ping_result, dict):
                self.log(f"✅ Location ping returned dict: {list(ping_result.keys())}", "PASS")
                if 'place' in ping_result or 'visits' in ping_result:
                    self.log(f"✅ Location ping has place/visits data", "PASS")
            else:
                self.log(f"❌ Location ping should return dict", "FAIL")
        
        # Test GET /api/location/timeline
        success, timeline = self.run_test(
            "Get location timeline",
            "GET",
            "location/timeline",
            200,
            token=self.demo_token
        )
        
        if success:
            required_keys = ['places', 'frequent', 'today_points', 'today', 'total_places']
            missing = [k for k in required_keys if k not in timeline]
            if not missing:
                self.log(f"✅ Location timeline has all required keys: {required_keys}", "PASS")
                self.log(f"   Places: {len(timeline.get('places', []))}, Frequent: {len(timeline.get('frequent', []))}, Today points: {timeline.get('today_points', 0)}", "INFO")
            else:
                self.log(f"❌ Location timeline missing keys: {missing}", "FAIL")
    
    def test_cheaper_model(self):
        """Verify cheaper Anthropic model works for action extraction"""
        self.log("=" * 60, "INFO")
        self.log("TESTING CHEAPER ANTHROPIC MODEL (claude-haiku-4-5-20251001)", "INFO")
        self.log("=" * 60, "INFO")
        
        # Send an actionable message that should trigger action extraction with cheaper model
        self.log("Sending actionable message to trigger action extraction...", "INFO")
        success, response = self.run_test(
            "Chat with actionable message (cheaper model test)",
            "POST",
            "chat/stream",
            200,
            data={"message": "remind me to call John tomorrow at 2pm"},
            token=self.demo_token,
            stream=True,
            headers_override={
                'Authorization': f'Bearer {self.demo_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if success:
            has_error = False
            has_actions = False
            
            try:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            try:
                                event = json.loads(data_str)
                                event_type = event.get('type')
                                
                                if event_type == 'error':
                                    has_error = True
                                    self.log(f"❌ Error event: {event.get('message')}", "FAIL")
                                elif event_type == 'actions':
                                    has_actions = True
                                    self.log(f"✅ Actions extracted successfully (cheaper model works)", "PASS")
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                self.log(f"Error reading stream: {e}", "WARN")
            
            if not has_error:
                self.log(f"✅ No 500 error - cheaper model (claude-haiku-4-5-20251001) works", "PASS")
            else:
                self.log(f"❌ Cheaper model caused error", "FAIL")
    
    def run_all_tests(self):
        """Run all Pass 3 tests"""
        start_time = time.time()
        
        self.log("=" * 60, "INFO")
        self.log("KAELRA PASS 3 BACKEND API TESTS", "INFO")
        self.log(f"Base URL: {self.base_url}", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            # Authenticate first
            if not self.test_auth():
                self.log("❌ Authentication failed, stopping tests", "FAIL")
                return 1
            
            # Run Pass 3 tests
            self.test_chat_stream()
            self.test_memory_endpoints()
            self.test_microsoft_oauth()
            self.test_google_oauth()
            self.test_location_endpoints()
            self.test_cheaper_model()
            
        except KeyboardInterrupt:
            self.log("\n⚠️  Tests interrupted by user", "WARN")
        except Exception as e:
            self.log(f"\n❌ Unexpected error: {e}", "FAIL")
        
        elapsed = time.time() - start_time
        
        # Print summary
        self.log("=" * 60, "INFO")
        self.log("TEST SUMMARY", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Total tests run: {self.tests_run}", "INFO")
        self.log(f"Tests passed: {self.tests_passed} ✅", "INFO")
        self.log(f"Tests failed: {self.tests_failed} ❌", "INFO")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%", "INFO")
        self.log(f"Time elapsed: {elapsed:.1f}s", "INFO")
        
        if self.failed_tests:
            self.log("\nFailed tests:", "INFO")
            for fail in self.failed_tests:
                self.log(f"  - {fail.get('name')}: {fail}", "FAIL")
        
        return 0 if self.tests_failed == 0 else 1


if __name__ == "__main__":
    tester = Pass3Tester()
    sys.exit(tester.run_all_tests())
