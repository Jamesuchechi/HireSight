from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.interviews.models import Interview, InterviewVideoSession, InterviewCodingSession
from apps.applications.models import Application
from apps.jobs.models import Job
from apps.accounts.models import CompanyProfile
import json
from unittest.mock import patch, MagicMock

User = get_user_model()

class LiveCodingTests(TestCase):
    def setUp(self):
        # Setup Users
        self.company_user = User.objects.create_user(email='company@test.com', password='password', account_type='company')
        self.candidate_user = User.objects.create_user(email='candidate@test.com', password='password', account_type='personal')
        
        # Setup Job & Application
        self.company_profile, _ = CompanyProfile.objects.get_or_create(
            user=self.company_user,
            defaults={'company_name': "Test Corp"}
        )
        self.job = Job.objects.create(company=self.company_profile, title="Developer", description="Code things")
        self.application = Application.objects.create(job=self.job, applicant=self.candidate_user)
        
        # Setup Interview
        self.interview = Interview.objects.create(
            application=self.application,
            interview_type='VIDEO',
            scheduled_date=timezone.now() + timedelta(days=1),
            use_inapp_video=True,
            interviewer_name="Test Interviewer",
            interviewer_email="interviewer@test.com"
        )
        
        # Setup Video Session
        self.video_session = InterviewVideoSession.objects.create(
            interview=self.interview,
            room_name=f"room_{self.interview.id}",
            live_coding_enabled=True
        )
        
        # Setup Coding Session
        self.coding_session = InterviewCodingSession.objects.create(
            video_session=self.video_session,
            language='python'
        )

        self.client = Client()

    def test_execute_code_unauthorized(self):
        url = reverse('interviews:execute_code')
        response = self.client.post(url, json.dumps({
            'code': 'print("hack")',
            'language': 'python',
            'interview_id': str(self.interview.id)
        }), content_type='application/json')
        
        # Should be 403 because we are not logged in
        self.assertEqual(response.status_code, 403)

    def test_execute_code_authorized(self):
        self.client.force_login(self.candidate_user)
        url = reverse('interviews:execute_code')
        
        # Mock docker execution
        with patch('apps.interviews.views.execute_python_code') as mock_exec:
            mock_exec.return_value = {'success': True, 'output': 'Hello'}
            
            response = self.client.post(url, json.dumps({
                'code': 'print("Hello")',
                'language': 'python',
                'interview_id': str(self.interview.id)
            }), content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['output'], 'Hello')
            
            # Verify result saved
            self.coding_session.refresh_from_db()
            self.assertEqual(self.coding_session.final_code, 'print("Hello")')
            self.assertEqual(self.coding_session.test_results, {'success': True, 'output': 'Hello'})

    def test_execute_javascript(self):
        self.client.force_login(self.candidate_user)
        url = reverse('interviews:execute_code')
        
        with patch('apps.interviews.views.execute_javascript_code') as mock_exec:
            mock_exec.return_value = {'success': True, 'output': 'Hello JS'}
            
            response = self.client.post(url, json.dumps({
                'code': 'console.log("Hello JS")',
                'language': 'javascript',
                'interview_id': str(self.interview.id)
            }), content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['output'], 'Hello JS')

    def test_execute_rust(self):
        self.client.force_login(self.candidate_user)
        url = reverse('interviews:execute_code')
        
        with patch('apps.interviews.views.execute_rust_code') as mock_exec:
            mock_exec.return_value = {'success': True, 'output': 'Hello Rust'}
            
            response = self.client.post(url, json.dumps({
                'code': 'println!("Hello Rust")',
                'language': 'rust',
                'interview_id': str(self.interview.id)
            }), content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['output'], 'Hello Rust')

    def test_execute_go(self):
        self.client.force_login(self.candidate_user)
        url = reverse('interviews:execute_code')
        with patch('apps.interviews.views.execute_go_code') as mock_exec:
            mock_exec.return_value = {'success': True, 'output': 'Hello Go'}
            response = self.client.post(url, json.dumps({
                'code': 'package main\nimport "fmt"\nfunc main() { fmt.Println("Hello Go") }',
                'language': 'go',
                'interview_id': str(self.interview.id)
            }), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['output'], 'Hello Go')

    def test_execute_cpp(self):
        self.client.force_login(self.candidate_user)
        url = reverse('interviews:execute_code')
        with patch('apps.interviews.views.execute_cpp_code') as mock_exec:
            mock_exec.return_value = {'success': True, 'output': 'Hello C++'}
            response = self.client.post(url, json.dumps({
                'code': '#include <iostream>\nint main() { std::cout << "Hello C++"; return 0; }',
                'language': 'cpp',
                'interview_id': str(self.interview.id)
            }), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['output'], 'Hello C++')

    def test_execute_php(self):
        self.client.force_login(self.candidate_user)
        url = reverse('interviews:execute_code')
        with patch('apps.interviews.views.execute_php_code') as mock_exec:
            mock_exec.return_value = {'success': True, 'output': 'Hello PHP'}
            response = self.client.post(url, json.dumps({
                'code': '<?php echo "Hello PHP"; ?>',
                'language': 'php',
                'interview_id': str(self.interview.id)
            }), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['output'], 'Hello PHP')

    def test_execute_ruby(self):
        self.client.force_login(self.candidate_user)
        url = reverse('interviews:execute_code')
        with patch('apps.interviews.views.execute_ruby_code') as mock_exec:
            mock_exec.return_value = {'success': True, 'output': 'Hello Ruby'}
            response = self.client.post(url, json.dumps({
                'code': 'puts "Hello Ruby"',
                'language': 'ruby',
                'interview_id': str(self.interview.id)
            }), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['output'], 'Hello Ruby')

    def test_save_snapshot(self):
        self.client.force_login(self.company_user)
        url = reverse('interviews:save_coding_session', args=[self.interview.id])
        
        response = self.client.post(url, json.dumps({
            'code': 'def foo(): pass',
            'language': 'python'
        }), content_type='application/json')
        

        self.assertEqual(response.status_code, 200)
        
        self.coding_session.refresh_from_db()
        self.assertEqual(self.coding_session.final_code, 'def foo(): pass')
        # Check history updated
        self.assertEqual(len(self.coding_session.code_history), 1)
        self.assertEqual(self.coding_session.code_history[0]['code'], 'def foo(): pass')

    def test_history_limit(self):
        self.client.force_login(self.company_user)
        url = reverse('interviews:save_coding_session', args=[self.interview.id])
        
        # Pre-fill history with 100 items
        self.coding_session.code_history = [{'idx': i} for i in range(100)]
        self.coding_session.save()
        
        # Add 101st item
        response = self.client.post(url, json.dumps({
            'code': 'new code',
            'language': 'python'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.coding_session.refresh_from_db()
        
        # Should still be 100
        self.assertEqual(len(self.coding_session.code_history), 100)
        # Last item should be the new one
        self.assertEqual(self.coding_session.code_history[-1]['code'], 'new code')
