from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from education.models import  Course, Module

class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_create_user_profile(self):
        """Тест: создание профиля пользователя и проверка роли"""
        profile = User.objects.create(user=self.user, is_teacher=False)
        self.assertEqual(profile.user.username, "testuser")
        self.assertFalse(profile.is_teacher)

class CourseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(username="teacher", password="testpass123")
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.teacher_profile = UserProfile.objects.create(user=self.teacher, is_teacher=True)
        self.user_profile = UserProfile.objects.create(user=self.user, is_teacher=False)
        self.course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            teacher=self.teacher_profile
        )

    def test_create_course(self):
        """Тест: создание курса"""
        course = Course.objects.create(
            title="New Course",
            description="New Description",
            teacher=self.teacher_profile
        )
        self.assertEqual(course.title, "New Course")
        self.assertEqual(course.description, "New Description")
        self.assertEqual(course.teacher, self.teacher_profile)

    def test_edit_course(self):
        """Тест: учитель может редактировать курс"""
        self.client.login(username="teacher", password="testpass123")
        response = self.client.post(reverse('edit_course', args=[self.course.id]), {
            'title': 'Updated Course',
            'description': 'Updated Description'
        })
        self.assertEqual(response.status_code, 302)  # Перенаправление после редактирования
        updated_course = Course.objects.get(id=self.course.id)
        self.assertEqual(updated_course.title, "Updated Course")
        self.assertEqual(updated_course.description, "Updated Description")

    def test_create_course_access_teacher(self):
        """Тест: учитель может зайти на страницу создания курса"""
        self.client.login(username="teacher", password="testpass123")
        response = self.client.get(reverse('create_course'))
        self.assertEqual(response.status_code, 200)  # Доступ разрешён

    def test_create_course_access_student(self):
        """Тест: студент не может зайти на страницу создания курса"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('create_course'))
        self.assertEqual(response.status_code, 302)  # Перенаправление (доступ запрещён)

    def test_create_course_page_get(self):
        """Тест: учитель может зайти на страницу создания курса (GET)"""
        self.client.login(username="teacher", password="testpass123")
        response = self.client.get(reverse('create_course'))
        self.assertEqual(response.status_code, 200)

    def test_create_course_submit(self):
        """Тест: учитель может создать курс (POST)"""
        self.client.login(username="teacher", password="testpass123")
        response = self.client.post(reverse('create_course'), {
            'title': 'Another Course',
            'description': 'Another Description'
        })
        self.assertEqual(response.status_code, 302)  # Перенаправление после создания
        self.assertTrue(Course.objects.filter(title="Another Course").exists())

class ModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(username="teacher", password="testpass123")
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.teacher_profile = UserProfile.objects.create(user=self.teacher, is_teacher=True)
        self.user_profile = UserProfile.objects.create(user=self.user, is_teacher=False)
        self.course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            teacher=self.teacher_profile
        )
        self.module = Module.objects.create(
            course=self.course,
            title="Test Module"
        )

    def test_create_module(self):
        """Тест: создание модуля в курсе"""
        module = Module.objects.create(
            course=self.course,
            title="Test Module"
        )
        self.assertEqual(module.title, "Test Module")
        self.assertEqual(module.course, self.course)

    def test_delete_module(self):
        """Тест: учитель может удалить модуль"""
        self.client.login(username="teacher", password="testpass123")
        response = self.client.post(reverse('delete_module', args=[self.module.id]))
        self.assertEqual(response.status_code, 302)  # Перенаправление после удаления
        self.assertFalse(Module.objects.filter(id=self.module.id).exists())  # Модуль удалён

    def test_module_detail_not_found(self):
        """Тест: доступ к несуществующему модулю"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('module_detail', args=[999]))  # Несуществующий ID
        self.assertEqual(response.status_code, 404)  # Ожидаем 404

class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_login_view(self):
        """Тест: вход пользователя"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Перенаправление после входа
        self.assertTrue('_auth_user_id' in self.client.session)  # Пользователь авторизован

    def test_logout_view(self):
        """Тест: выход пользователя"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Перенаправление после выхода
        self.assertFalse('_auth_user_id' in self.client.session)  # Пользователь разлогинен


    def test_register_password_mismatch(self):
        """Тест: регистрация с несовпадающими паролями"""
        response = self.client.post(reverse('signup'), {
            'username': 'newstudent',
            'password1': 'newpass123',
            'password2': 'differentpass'
        })
        self.assertEqual(response.status_code, 200)  # Остаёмся на странице регистрации
        self.assertFalse(User.objects.filter(username="newstudent").exists())

    def test_login_invalid_password(self):
        """Тест: вход с неправильным паролем"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)  # Остаёмся на странице логина
        self.assertFalse('_auth_user_id' in self.client.session)  # Пользователь не авторизован

class ProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.user_profile = UserProfile.objects.create(user=self.user, is_teacher=False)

    def test_profile_access(self):
        """Тест: пользователь может зайти на страницу профиля"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 200)  # Доступ разрешён

    def test_profile_access_unauthenticated(self):
        """Тест: неавторизованный пользователь не может зайти на страницу профиля"""
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 302)  # Перенаправление на логин