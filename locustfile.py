from locust import HttpUser, task, between

class EducationPlatformUser(HttpUser):
    # Время ожидания между действиями пользователя (от 1 до 5 секунд)
    wait_time = between(1, 5)

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

    @task(3)
    def view_module(self):
        """Симуляция просмотра модуля"""
        self.client.get('/module/1/')  # Предполагаем, что модуль с ID=1 существует

    @task(1)
    def create_course(self):
        """Симуляция попытки создать курс (доступно только учителям, ожидаем 403 для студента)"""
        response = self.client.get('/course/create/')
        if 'csrftoken' in response.cookies:
            csrftoken = response.cookies['csrftoken']
            self.client.post(
                '/course/create/',
                {'title': 'Test Course', 'description': 'Test Description'},
                headers={'X-CSRFToken': csrftoken, 'Referer': self.host + '/course/create/'}
            )