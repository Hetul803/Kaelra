"""Comprehensive backend API tests for Kaelra Personal AI Operator.

Tests all endpoints: auth, onboarding, dashboard, briefing (LLM), chat (SSE),
actions, memory, goals, routines, files (LLM), accounts, devices, notifications,
audit, and privacy.
"""

import requests
import json
import sys
import time
from datetime import datetime
from io import BytesIO

BASE_URL = "https://kaelra-operator.preview.emergentagent.com/api"

class KaelraAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.demo_token = None
        self.throwaway_token = None
        self.throwaway_email = None
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []
        
    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, 
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
                if files:
                    # Remove Content-Type for multipart
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=headers, timeout=60)
                else:
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
    
    # ==================== AUTH TESTS ====================
    def test_auth(self):
        """Test authentication endpoints"""
        self.log("=" * 60, "INFO")
        self.log("TESTING AUTH ENDPOINTS", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test demo login
        success, response = self.run_test(
            "Demo Login",
            "POST",
            "auth/demo",
            200
        )
        if success and 'token' in response:
            self.demo_token = response['token']
            self.log(f"Demo token obtained: {self.demo_token[:20]}...", "INFO")
        
        # Test signup with throwaway account
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.throwaway_email = f"test_{timestamp}@example.com"
        success, response = self.run_test(
            "Signup (new user)",
            "POST",
            "auth/signup",
            200,
            data={
                "email": self.throwaway_email,
                "password": "TestPass123!",
                "name": "Test User"
            }
        )
        if success and 'token' in response:
            self.throwaway_token = response['token']
            self.log(f"Throwaway user created: {self.throwaway_email}", "INFO")
            # Verify onboarded=false
            if response.get('user', {}).get('onboarded') == False:
                self.log("✅ New user onboarded=false verified", "PASS")
            else:
                self.log("❌ New user should have onboarded=false", "FAIL")
        
        # Test duplicate signup
        self.run_test(
            "Signup (duplicate email)",
            "POST",
            "auth/signup",
            400,
            data={
                "email": self.throwaway_email,
                "password": "TestPass123!",
                "name": "Test User"
            }
        )
        
        # Test login with correct password
        self.run_test(
            "Login (correct password)",
            "POST",
            "auth/login",
            200,
            data={
                "email": "demo@kaelra.ai",
                "password": "kaelra"
            }
        )
        
        # Test login with wrong password
        self.run_test(
            "Login (wrong password)",
            "POST",
            "auth/login",
            401,
            data={
                "email": "demo@kaelra.ai",
                "password": "wrongpassword"
            }
        )
        
        # Test /auth/me with valid token
        success, response = self.run_test(
            "Get current user (with token)",
            "GET",
            "auth/me",
            200,
            token=self.demo_token
        )
        if success:
            if 'user' in response and 'profile' in response:
                self.log("✅ /auth/me returns user + profile", "PASS")
            else:
                self.log("❌ /auth/me should return user + profile", "FAIL")
        
        # Test /auth/me without token
        self.run_test(
            "Get current user (no token)",
            "GET",
            "auth/me",
            401
        )
    
    # ==================== ONBOARDING TESTS ====================
    def test_onboarding(self):
        """Test onboarding endpoint"""
        self.log("=" * 60, "INFO")
        self.log("TESTING ONBOARDING", "INFO")
        self.log("=" * 60, "INFO")
        
        if not self.throwaway_token:
            self.log("⚠️  Skipping onboarding test (no throwaway token)", "WARN")
            return
        
        success, response = self.run_test(
            "Save onboarding profile",
            "POST",
            "onboarding",
            200,
            data={
                "name": "Test User",
                "call_me": "Tester",
                "routine": "Work 9-5, gym at 6pm",
                "tone": "friendly",
                "interests": ["tech", "fitness"],
                "life_areas": ["career", "health"],
                "goals": ["Learn Python", "Get fit"],
                "notifications_enabled": True,
                "device_sync": True,
                "proactive_briefing": True
            },
            token=self.throwaway_token
        )
        
        if success:
            if response.get('user', {}).get('onboarded') == True:
                self.log("✅ User marked as onboarded=true", "PASS")
            else:
                self.log("❌ User should be marked onboarded=true", "FAIL")
            
            # Verify goals were seeded
            goals_success, goals = self.run_test(
                "Verify goals seeded",
                "GET",
                "goals",
                200,
                token=self.throwaway_token
            )
            if goals_success and len(goals) >= 2:
                self.log(f"✅ Goals seeded: {len(goals)} goals found", "PASS")
            
            # Verify memories were seeded
            mem_success, memories = self.run_test(
                "Verify memories seeded",
                "GET",
                "memories",
                200,
                token=self.throwaway_token
            )
            if mem_success and 'memories' in memories and len(memories['memories']) > 0:
                self.log(f"✅ Memories seeded: {len(memories['memories'])} memories found", "PASS")
    
    # ==================== DASHBOARD TESTS ====================
    def test_dashboard(self):
        """Test dashboard endpoint"""
        self.log("=" * 60, "INFO")
        self.log("TESTING DASHBOARD", "INFO")
        self.log("=" * 60, "INFO")
        
        success, response = self.run_test(
            "Get dashboard",
            "GET",
            "dashboard",
            200,
            token=self.demo_token
        )
        
        if success:
            required_keys = ['profile', 'cards', 'action_counts', 'devices']
            missing = [k for k in required_keys if k not in response]
            if not missing:
                self.log(f"✅ Dashboard has all required keys: {required_keys}", "PASS")
            else:
                self.log(f"❌ Dashboard missing keys: {missing}", "FAIL")
            
            # Check cards structure
            if 'cards' in response:
                cards = response['cards']
                expected_cards = ['calendar', 'emails', 'commute', 'news', 'goals', 'reminders', 
                                'files_needing_attention', 'pending_actions']
                found_cards = [k for k in expected_cards if k in cards]
                self.log(f"✅ Dashboard cards found: {found_cards}", "PASS")
    
    # ==================== BRIEFING TESTS (LLM) ====================
    def test_briefing(self):
        """Test briefing engine (LLM)"""
        self.log("=" * 60, "INFO")
        self.log("TESTING BRIEFING ENGINE (LLM)", "INFO")
        self.log("=" * 60, "INFO")
        
        # First briefing generation
        self.log("Generating briefing (may take ~30s)...", "INFO")
        success, response = self.run_test(
            "Generate briefing",
            "POST",
            "briefing",
            200,
            token=self.demo_token
        )
        
        if success:
            if 'briefing' in response:
                briefing = response['briefing']
                if 'greeting' in briefing:
                    self.log(f"✅ Briefing greeting: {briefing['greeting'][:100]}...", "PASS")
                if 'actions_prepared' in briefing:
                    self.log(f"✅ Actions prepared: {briefing['actions_prepared']}", "PASS")
            
            if 'action_counts' in response:
                self.log(f"✅ Action counts returned: {response['action_counts']}", "PASS")
        
        # Test cached briefing (should be instant)
        start = time.time()
        success, response = self.run_test(
            "Get cached briefing (dashboard)",
            "GET",
            "dashboard",
            200,
            token=self.demo_token
        )
        elapsed = time.time() - start
        if success and 'briefing' in response and elapsed < 2:
            self.log(f"✅ Cached briefing returned instantly ({elapsed:.2f}s)", "PASS")
        
        # Test force regenerate
        self.log("Force regenerating briefing (may take ~30s)...", "INFO")
        self.run_test(
            "Force regenerate briefing",
            "POST",
            "briefing?force=true",
            200,
            token=self.demo_token
        )
    
    # ==================== CHAT TESTS (SSE) ====================
    def test_chat(self):
        """Test chat streaming (SSE)"""
        self.log("=" * 60, "INFO")
        self.log("TESTING CHAT STREAMING (SSE)", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test chat stream
        self.log("Streaming chat message (may take ~30s)...", "INFO")
        success, response = self.run_test(
            "Chat stream",
            "POST",
            "chat/stream",
            200,
            data={"message": "When should I leave for work today?"},
            token=self.demo_token,
            stream=True,
            headers_override={
                'Authorization': f'Bearer {self.demo_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if success:
            session_id = None
            delta_count = 0
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
                                    session_id = event.get('session_id')
                                    self.log(f"✅ Session created: {session_id}", "PASS")
                                elif event_type == 'delta':
                                    delta_count += 1
                                elif event_type == 'actions':
                                    self.log(f"✅ Actions event received: {len(event.get('actions', []))} actions", "PASS")
                                elif event_type == 'done':
                                    has_done = True
                                    self.log("✅ Done event received", "PASS")
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                self.log(f"Error reading stream: {e}", "WARN")
            
            if delta_count > 0:
                self.log(f"✅ Received {delta_count} delta events with reply text", "PASS")
            else:
                self.log("❌ No delta events received", "FAIL")
            
            if has_done:
                self.log("✅ Stream completed with 'done' event", "PASS")
            
            # Test list sessions
            if session_id:
                success, sessions = self.run_test(
                    "List chat sessions",
                    "GET",
                    "chat/sessions",
                    200,
                    token=self.demo_token
                )
                if success and len(sessions) > 0:
                    self.log(f"✅ Found {len(sessions)} chat sessions", "PASS")
                
                # Test get messages
                success, messages = self.run_test(
                    "Get session messages",
                    "GET",
                    f"chat/sessions/{session_id}/messages",
                    200,
                    token=self.demo_token
                )
                if success and len(messages) >= 2:
                    self.log(f"✅ Found {len(messages)} messages (user + assistant)", "PASS")
    
    # ==================== ACTION QUEUE TESTS ====================
    def test_actions(self):
        """Test action queue"""
        self.log("=" * 60, "INFO")
        self.log("TESTING ACTION QUEUE", "INFO")
        self.log("=" * 60, "INFO")
        
        # List pending actions
        success, actions = self.run_test(
            "List pending actions",
            "GET",
            "actions?status=pending",
            200,
            token=self.demo_token
        )
        
        action_id = None
        if success and len(actions) > 0:
            self.log(f"✅ Found {len(actions)} pending actions", "PASS")
            action_id = actions[0].get('id')
        
        # Create a user action with unique title
        timestamp = int(time.time())
        success, created = self.run_test(
            "Create user action",
            "POST",
            "actions",
            200,
            data={
                "type": "reminder",
                "title": f"Test reminder {timestamp}",
                "what": "Test action from API test",
                "when": "2025-08-20T10:00:00Z"
            },
            token=self.demo_token
        )
        
        if success and 'id' in created:
            action_id = created['id']
            self.log(f"✅ Action created with ID: {action_id}", "PASS")
        
        if action_id:
            # Test approve action
            success, updated = self.run_test(
                "Approve action",
                "PUT",
                f"actions/{action_id}",
                200,
                data={"status": "approved"},
                token=self.demo_token
            )
            if success and updated.get('status') == 'approved':
                self.log("✅ Action approved successfully", "PASS")
            
            # Create another action for reject test
            timestamp2 = int(time.time()) + 1
            success, created2 = self.run_test(
                "Create action for reject",
                "POST",
                "actions",
                200,
                data={
                    "type": "reminder",
                    "title": f"Test reject {timestamp2}",
                    "what": "Will be rejected",
                    "when": "2025-08-20T11:00:00Z"
                },
                token=self.demo_token
            )
            
            if success and 'id' in created2:
                # Test reject action
                self.run_test(
                    "Reject action",
                    "PUT",
                    f"actions/{created2['id']}",
                    200,
                    data={"status": "rejected"},
                    token=self.demo_token
                )
            
            # Create another for snooze test
            timestamp3 = int(time.time()) + 2
            success, created3 = self.run_test(
                "Create action for snooze",
                "POST",
                "actions",
                200,
                data={
                    "type": "reminder",
                    "title": f"Test snooze {timestamp3}",
                    "what": "Will be snoozed",
                    "when": "2025-08-20T12:00:00Z"
                },
                token=self.demo_token
            )
            
            if success and 'id' in created3:
                # Test snooze action
                self.run_test(
                    "Snooze action",
                    "PUT",
                    f"actions/{created3['id']}",
                    200,
                    data={"status": "snoozed"},
                    token=self.demo_token
                )
            
            # Test edit action
            timestamp4 = int(time.time()) + 3
            success, created4 = self.run_test(
                "Create action for edit",
                "POST",
                "actions",
                200,
                data={
                    "type": "reminder",
                    "title": f"Original title {timestamp4}",
                    "what": "Original what",
                    "when": "2025-08-20T13:00:00Z"
                },
                token=self.demo_token
            )
            
            if success and 'id' in created4:
                self.run_test(
                    "Edit action",
                    "PUT",
                    f"actions/{created4['id']}",
                    200,
                    data={"title": "Updated title", "what": "Updated what"},
                    token=self.demo_token
                )
    
    # ==================== MEMORY TESTS ====================
    def test_memories(self):
        """Test memory CRUD"""
        self.log("=" * 60, "INFO")
        self.log("TESTING MEMORY CRUD", "INFO")
        self.log("=" * 60, "INFO")
        
        # List memories
        success, response = self.run_test(
            "List memories",
            "GET",
            "memories",
            200,
            token=self.demo_token
        )
        
        if success:
            if 'categories' in response and len(response['categories']) == 10:
                self.log(f"✅ 10 memory categories returned", "PASS")
            if 'memories' in response:
                self.log(f"✅ Found {len(response['memories'])} memories", "PASS")
        
        # Create memory
        success, created = self.run_test(
            "Create memory",
            "POST",
            "memories",
            200,
            data={
                "category": "Personal facts",
                "content": "Test memory from API test",
                "important": False,
                "temporary": False
            },
            token=self.demo_token
        )
        
        memory_id = None
        if success and 'id' in created:
            memory_id = created['id']
            self.log(f"✅ Memory created with ID: {memory_id}", "PASS")
        
        if memory_id:
            # Update memory (mark important)
            success, updated = self.run_test(
                "Mark memory important",
                "PUT",
                f"memories/{memory_id}",
                200,
                data={"important": True},
                token=self.demo_token
            )
            if success and updated.get('important') == True:
                self.log("✅ Memory marked important", "PASS")
            
            # Update memory (mark temporary)
            self.run_test(
                "Mark memory temporary",
                "PUT",
                f"memories/{memory_id}",
                200,
                data={"temporary": True},
                token=self.demo_token
            )
            
            # Delete memory
            self.run_test(
                "Delete memory",
                "DELETE",
                f"memories/{memory_id}",
                200,
                token=self.demo_token
            )
    
    # ==================== GOALS TESTS ====================
    def test_goals(self):
        """Test goals CRUD"""
        self.log("=" * 60, "INFO")
        self.log("TESTING GOALS CRUD", "INFO")
        self.log("=" * 60, "INFO")
        
        # List goals
        success, goals = self.run_test(
            "List goals",
            "GET",
            "goals",
            200,
            token=self.demo_token
        )
        if success:
            self.log(f"✅ Found {len(goals)} goals", "PASS")
        
        # Create goal
        success, created = self.run_test(
            "Create goal",
            "POST",
            "goals",
            200,
            data={
                "title": "Test goal from API",
                "description": "Testing goal creation",
                "progress": 0.0,
                "target_date": "2025-12-31"
            },
            token=self.demo_token
        )
        
        goal_id = None
        if success and 'id' in created:
            goal_id = created['id']
            self.log(f"✅ Goal created with ID: {goal_id}", "PASS")
        
        if goal_id:
            # Update goal
            success, updated = self.run_test(
                "Update goal progress",
                "PUT",
                f"goals/{goal_id}",
                200,
                data={"progress": 0.5},
                token=self.demo_token
            )
            if success and updated.get('progress') == 0.5:
                self.log("✅ Goal progress updated", "PASS")
            
            # Delete goal
            self.run_test(
                "Delete goal",
                "DELETE",
                f"goals/{goal_id}",
                200,
                token=self.demo_token
            )
    
    # ==================== ROUTINES TESTS ====================
    def test_routines(self):
        """Test routines CRUD"""
        self.log("=" * 60, "INFO")
        self.log("TESTING ROUTINES CRUD", "INFO")
        self.log("=" * 60, "INFO")
        
        # List routines
        success, routines = self.run_test(
            "List routines",
            "GET",
            "routines",
            200,
            token=self.demo_token
        )
        if success:
            self.log(f"✅ Found {len(routines)} routines", "PASS")
        
        # Create routine
        success, created = self.run_test(
            "Create routine",
            "POST",
            "routines",
            200,
            data={
                "name": "Test routine",
                "description": "Testing routine creation",
                "time": "09:00",
                "days": ["monday", "wednesday", "friday"],
                "enabled": True
            },
            token=self.demo_token
        )
        
        routine_id = None
        if success and 'id' in created:
            routine_id = created['id']
            self.log(f"✅ Routine created with ID: {routine_id}", "PASS")
        
        if routine_id:
            # Toggle routine
            success, updated = self.run_test(
                "Toggle routine (disable)",
                "PUT",
                f"routines/{routine_id}",
                200,
                data={"enabled": False},
                token=self.demo_token
            )
            if success and updated.get('enabled') == False:
                self.log("✅ Routine disabled", "PASS")
            
            # Delete routine
            self.run_test(
                "Delete routine",
                "DELETE",
                f"routines/{routine_id}",
                200,
                token=self.demo_token
            )
    
    # ==================== FILES TESTS (LLM) ====================
    def test_files(self):
        """Test files with LLM summarization"""
        self.log("=" * 60, "INFO")
        self.log("TESTING FILES (LLM)", "INFO")
        self.log("=" * 60, "INFO")
        
        # Create a test file with deadlines
        file_content = """Project Deadline Document
        
Assignment 1: Due August 25, 2025
Contact: John Doe (john@example.com)

Assignment 2: Due September 1, 2025
Contact: Jane Smith (jane@example.com)

Key action items:
- Review code by August 20
- Submit final report by August 30
- Schedule meeting with team
"""
        
        # Upload file
        self.log("Uploading file (LLM summarization may take ~30s)...", "INFO")
        files_data = {
            'file': ('test_deadlines.txt', BytesIO(file_content.encode()), 'text/plain')
        }
        
        success, response = self.run_test(
            "Upload file with LLM summary",
            "POST",
            "files/upload",
            200,
            files=files_data,
            token=self.demo_token
        )
        
        file_id = None
        if success:
            if 'file' in response and 'id' in response['file']:
                file_id = response['file']['id']
                self.log(f"✅ File uploaded with ID: {file_id}", "PASS")
            
            if 'summary' in response:
                summary = response['summary']
                if 'summary' in summary:
                    self.log(f"✅ Summary generated: {summary['summary'][:100]}...", "PASS")
                if 'people' in summary and len(summary['people']) > 0:
                    self.log(f"✅ People extracted: {summary['people']}", "PASS")
                if 'deadlines' in summary and len(summary['deadlines']) > 0:
                    self.log(f"✅ Deadlines extracted: {len(summary['deadlines'])} deadlines", "PASS")
                if 'action_items' in summary and len(summary['action_items']) > 0:
                    self.log(f"✅ Action items extracted: {len(summary['action_items'])} items", "PASS")
            
            # Check if assignment_reminder actions were prepared
            success_actions, actions = self.run_test(
                "Check assignment_reminder actions",
                "GET",
                "actions?status=pending",
                200,
                token=self.demo_token
            )
            if success_actions:
                reminder_actions = [a for a in actions if a.get('type') == 'assignment_reminder']
                if len(reminder_actions) > 0:
                    self.log(f"✅ {len(reminder_actions)} assignment_reminder actions prepared", "PASS")
        
        # List files
        success, files_list = self.run_test(
            "List files",
            "GET",
            "files",
            200,
            token=self.demo_token
        )
        if success and len(files_list) > 0:
            self.log(f"✅ Found {len(files_list)} files with summaries", "PASS")
        
        if file_id:
            # Ask about file
            self.log("Asking question about file (LLM may take ~30s)...", "INFO")
            success, answer = self.run_test(
                "Ask about file",
                "POST",
                f"files/{file_id}/ask",
                200,
                data={"question": "What are the deadlines in this file?"},
                token=self.demo_token
            )
            if success and 'answer' in answer:
                self.log(f"✅ Answer received: {answer['answer'][:100]}...", "PASS")
            
            # Mark important
            success, updated = self.run_test(
                "Mark file important",
                "PUT",
                f"files/{file_id}/important?important=true",
                200,
                token=self.demo_token
            )
            if success and updated.get('important') == True:
                self.log("✅ File marked important", "PASS")
            
            # Delete file
            self.run_test(
                "Delete file",
                "DELETE",
                f"files/{file_id}",
                200,
                token=self.demo_token
            )
    
    # ==================== CONNECTED ACCOUNTS TESTS ====================
    def test_accounts(self):
        """Test connected accounts"""
        self.log("=" * 60, "INFO")
        self.log("TESTING CONNECTED ACCOUNTS", "INFO")
        self.log("=" * 60, "INFO")
        
        # List accounts
        success, accounts = self.run_test(
            "List connected accounts",
            "GET",
            "accounts",
            200,
            token=self.demo_token
        )
        
        if success and len(accounts) > 0:
            self.log(f"✅ Found {len(accounts)} connectors", "PASS")
            
            # Check for expected connectors
            providers = [a.get('provider') for a in accounts]
            expected = ['calendar', 'gmail', 'drive', 'maps', 'news']
            found = [p for p in expected if p in providers]
            self.log(f"✅ Mock connectors found: {found}", "PASS")
            
            # Find a not_connected connector (github)
            github = next((a for a in accounts if a.get('provider') == 'github'), None)
            if github and github.get('status') == 'not_connected':
                # Test connect
                success, updated = self.run_test(
                    "Connect account (github)",
                    "PUT",
                    "accounts/github",
                    200,
                    data={"status": "connected"},
                    token=self.demo_token
                )
                if success and updated.get('status') == 'connected':
                    self.log("✅ Account connected", "PASS")
                
                # Test disconnect
                self.run_test(
                    "Disconnect account (github)",
                    "PUT",
                    "accounts/github",
                    200,
                    data={"status": "not_connected"},
                    token=self.demo_token
                )
            
            # Find a coming_soon connector (smart_home)
            coming_soon = next((a for a in accounts if a.get('status') == 'coming_soon'), None)
            if coming_soon:
                # Test connecting coming_soon (should fail with 400)
                self.run_test(
                    "Connect coming_soon account (should fail)",
                    "PUT",
                    f"accounts/{coming_soon['provider']}",
                    400,
                    data={"status": "connected"},
                    token=self.demo_token
                )
    
    # ==================== DEVICES TESTS ====================
    def test_devices(self):
        """Test devices"""
        self.log("=" * 60, "INFO")
        self.log("TESTING DEVICES", "INFO")
        self.log("=" * 60, "INFO")
        
        # Register device heartbeat
        device_id = f"test_device_{int(time.time())}"
        success, device = self.run_test(
            "Register device heartbeat",
            "POST",
            "devices/heartbeat",
            200,
            data={
                "device_id": device_id,
                "name": "Test Device",
                "kind": "web",
                "voice_enabled": False
            },
            token=self.demo_token
        )
        if success and 'id' in device:
            self.log(f"✅ Device registered: {device_id}", "PASS")
        
        # List devices
        success, devices = self.run_test(
            "List devices",
            "GET",
            "devices",
            200,
            token=self.demo_token
        )
        if success and len(devices) >= 2:
            self.log(f"✅ Found {len(devices)} devices (demo has 2+)", "PASS")
    
    # ==================== NOTIFICATIONS TESTS ====================
    def test_notifications(self):
        """Test notifications"""
        self.log("=" * 60, "INFO")
        self.log("TESTING NOTIFICATIONS", "INFO")
        self.log("=" * 60, "INFO")
        
        # Create notification
        success, created = self.run_test(
            "Create notification",
            "POST",
            "notifications",
            200,
            data={
                "title": "Test reminder",
                "body": "This is a test notification",
                "type": "reminder",
                "scheduled_for": "2025-08-20T15:00:00Z"
            },
            token=self.demo_token
        )
        
        notification_id = None
        if success and 'id' in created:
            notification_id = created['id']
            self.log(f"✅ Notification created with ID: {notification_id}", "PASS")
        
        # List notifications
        success, notifications = self.run_test(
            "List notifications",
            "GET",
            "notifications",
            200,
            token=self.demo_token
        )
        if success:
            self.log(f"✅ Found {len(notifications)} notifications", "PASS")
        
        if notification_id:
            # Mark as read
            success, result = self.run_test(
                "Mark notification read",
                "PUT",
                f"notifications/{notification_id}/read",
                200,
                token=self.demo_token
            )
            if success and result.get('ok'):
                self.log("✅ Notification marked as read", "PASS")
            
            # Delete notification
            self.run_test(
                "Delete notification",
                "DELETE",
                f"notifications/{notification_id}",
                200,
                token=self.demo_token
            )
    
    # ==================== AUDIT LOG TESTS ====================
    def test_audit(self):
        """Test audit log"""
        self.log("=" * 60, "INFO")
        self.log("TESTING AUDIT LOG", "INFO")
        self.log("=" * 60, "INFO")
        
        success, events = self.run_test(
            "Get audit log",
            "GET",
            "audit",
            200,
            token=self.demo_token
        )
        
        if success and len(events) > 0:
            self.log(f"✅ Found {len(events)} audit events", "PASS")
            
            # Check for expected event types
            event_types = [e.get('event_type') for e in events]
            expected_types = ['action.prepared', 'briefing.generated', 'auth.login']
            found_types = [t for t in expected_types if t in event_types]
            if found_types:
                self.log(f"✅ Found event types: {found_types}", "PASS")
    
    # ==================== PRIVACY TESTS ====================
    def test_privacy(self):
        """Test privacy endpoints (export and delete)"""
        self.log("=" * 60, "INFO")
        self.log("TESTING PRIVACY", "INFO")
        self.log("=" * 60, "INFO")
        
        if not self.throwaway_token:
            self.log("⚠️  Skipping privacy tests (no throwaway token)", "WARN")
            return
        
        # Test export
        success, export_data = self.run_test(
            "Export user data",
            "GET",
            "privacy/export",
            200,
            token=self.throwaway_token
        )
        
        if success:
            if 'user' in export_data:
                self.log("✅ Export includes user data", "PASS")
            
            collections = ['profiles', 'memories', 'goals', 'routines', 'actions', 
                         'notifications', 'files', 'messages', 'audit_log', 
                         'connected_accounts', 'devices']
            found_collections = [c for c in collections if c in export_data]
            self.log(f"✅ Export includes {len(found_collections)} collections", "PASS")
        
        # Test delete (on throwaway user only!)
        self.log("⚠️  Deleting throwaway user data...", "WARN")
        success, result = self.run_test(
            "Delete user data (throwaway)",
            "DELETE",
            "privacy/data",
            200,
            token=self.throwaway_token
        )
        
        if success and result.get('ok'):
            self.log("✅ User data deleted successfully", "PASS")
            
            # Verify data is deleted
            success, memories = self.run_test(
                "Verify memories deleted",
                "GET",
                "memories",
                200,
                token=self.throwaway_token
            )
            if success and 'memories' in memories and len(memories['memories']) == 0:
                self.log("✅ Memories wiped after delete", "PASS")
    
    # ==================== RUN ALL TESTS ====================
    def run_all_tests(self):
        """Run all test suites"""
        start_time = time.time()
        
        self.log("=" * 60, "INFO")
        self.log("KAELRA BACKEND API TEST SUITE", "INFO")
        self.log(f"Base URL: {self.base_url}", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            self.test_auth()
            self.test_onboarding()
            self.test_dashboard()
            self.test_briefing()
            self.test_chat()
            self.test_actions()
            self.test_memories()
            self.test_goals()
            self.test_routines()
            self.test_files()
            self.test_accounts()
            self.test_devices()
            self.test_notifications()
            self.test_audit()
            self.test_privacy()
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
    tester = KaelraAPITester()
    sys.exit(tester.run_all_tests())
