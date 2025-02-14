from django.test import TestCase
from .models import User, UserProfile, Course, Module, Content, Quiz, Question, Answer

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user_profile = UserProfile.objects.create(user=self.user, is_teacher=True)
        self.course = Course.objects.create(title='Test Course', description='Test Description', teacher=self.user_profile)
        self.module = Module.objects.create(title='Test Module', description='Test Description', course=self.course)
        self.content = Content.objects.create(module=self.module, content_type='text', text='Test Content')
        self.quiz = Quiz.objects.create(module=self.module, title='Test Quiz')
        self.question = Question.objects.create(quiz=self.quiz, text='Test Question')
        self.answer = Answer.objects.create(question=self.question, text='Test Answer', is_correct=True)

    def test_course_creation(self):
        self.assertEqual(self.course.title, 'Test Course')
        self.assertEqual(self.course.teacher, self.user_profile)

    def test_quiz_creation(self):
        self.assertEqual(self.quiz.title, 'Test Quiz')
        self.assertEqual(self.quiz.module, self.module)

    def test_question_creation(self):
        self.assertEqual(self.question.text, 'Test Question')
        self.assertEqual(self.question.quiz, self.quiz)

    def test_answer_creation(self):
        self.assertEqual(self.answer.text, 'Test Answer')
        self.assertTrue(self.answer.is_correct)