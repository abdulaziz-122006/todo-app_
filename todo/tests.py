from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from todo.models import Task

class TaskNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()
        self.client.login(username='testuser', password='password123')

    def test_add_task_with_due_date(self):
        now = timezone.now()
        due_str = (now + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post('/add/', {
            'title': 'Test Timed Task',
            'priority': 'Yuqori',
            'due_date': due_str
        })
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='Test Timed Task')
        self.assertIsNotNone(task.due_date)
        self.assertFalse(task.notified)

    def test_get_due_tasks(self):
        # Create a past due task that has not been notified
        past_time = timezone.now() - timedelta(minutes=5)
        Task.objects.create(
            user=self.user,
            title='Overdue Task',
            priority='Yuqori',
            due_date=past_time,
            notified=False
        )

        response = self.client.get('/api/due-tasks/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['title'], 'Overdue Task')

    def test_mark_notified(self):
        task = Task.objects.create(
            user=self.user,
            title='Mark me',
            due_date=timezone.now() - timedelta(minutes=1),
            notified=False
        )
        response = self.client.post(f'/mark-notified/{task.id}/')
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertTrue(task.notified)

    def test_snooze_task(self):
        task = Task.objects.create(
            user=self.user,
            title='Snooze me',
            due_date=timezone.now() - timedelta(minutes=1),
            notified=True
        )
        response = self.client.post(f'/snooze/{task.id}/', {'minutes': 15})
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertFalse(task.notified)
        self.assertGreater(task.due_date, timezone.now())

    def test_service_worker_endpoint(self):
        response = self.client.get('/sw.js')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/javascript')

    def test_google_login_unconfigured(self):
        with self.settings(GOOGLE_CLIENT_ID='', GOOGLE_CLIENT_SECRET=''):
            response = self.client.get('/google/login/')
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)

    def test_google_login_redirect_to_google(self):
        with self.settings(GOOGLE_CLIENT_ID='test-client-id', GOOGLE_CLIENT_SECRET='test-secret'):
            response = self.client.get('/google/login/')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('https://accounts.google.com/o/oauth2/v2/auth'))
            self.assertIn('test-client-id', response.url)
            self.assertIn('google_oauth_state', self.client.session)

    def test_google_callback_invalid_state(self):
        session = self.client.session
        session['google_oauth_state'] = 'valid-state-123'
        session.save()

        response = self.client.get('/google/callback/?code=some-code&state=wrong-state')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

