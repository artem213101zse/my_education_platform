from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Пауза между задачами 1-5 секунд

    def on_start(self):
        """Выполняется при старте каждого пользователя"""
        self.login()

    def login(self):
        """Симуляция входа пользователя"""
        # Получаем CSRF-токен со страницы логина
        response = self.client.get('/login/')
        csrftoken = response.cookies['csrftoken']

        # Выполняем вход (для студента)
        self.client.post(
            '/login/',
            {'username': 'admin', 'password': 'admin'},
            headers={'X-CSRFToken': csrftoken, 'Referer': self.host + '/login/'}
        )


    @task(1)
    def register(self):
        """Тест: Регистрация нового пользователя"""
        self.client.get("/signup/")
        csrftoken = self.client.cookies.get('csrftoken', None)
        self.client.post(
            "/signup/",
            {"username":"teacher", "password1": "newpass123", "password2": "newpass123"},
            headers={"X-CSRFToken": csrftoken}
        )

    @task(3)
    def view_module(self):
        """Тест: Просмотр модуля"""
        self.client.get("/module/1/")

    @task(1)
    def create_course(self):
        """Тест: Создание курса (учитель)"""
        self.teacher_client.get("/course/create/")
        self.teacher_client.post(
            "/course/create/",
            {"title": "New Course", "description": "Course Description"},
            headers={"X-CSRFToken": self.teacher_csrftoken}
        )


    @task(2)
    def view_profile(self):
        """Тест: Просмотр профиля"""
        self.client.get("/profile/")