from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название курса')
    description = models.TextField(verbose_name='Описание курса')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_courses', verbose_name='Автор курса')
    participants = models.ManyToManyField(User, related_name='enrolled_courses', blank=True, verbose_name='Участники курса')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self):
        return self.title

class Module(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название модуля')
    description = models.TextField(verbose_name='Описание модуля')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name='Курс к которому принадлежит модуль')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок модуля в списке')

    class Meta:
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модули'

    def __str__(self):
        return self.title

class Content(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='contents', verbose_name='Модуль')
    content_type = models.CharField(max_length=50, choices=[
        ('text', 'Текст'),
        ('video', 'Видео'),
        ('image', 'Изображение'),
        ('file', 'Файл')
    ], verbose_name='Тип контента')
    title = models.CharField(max_length=200, blank=True, default='', verbose_name='Название')
    text = models.TextField(blank=True, null=True, verbose_name='Текст')
    video_url = models.URLField(blank=True, null=True, verbose_name='Ссылка на видео')
    video_file = models.FileField(upload_to='content_videos/', blank=True, null=True, verbose_name='Прикрепить видео')
    image = models.ImageField(upload_to='content_images/', blank=True, null=True, verbose_name='Изображение')
    file = models.FileField(upload_to='content_files/', blank=True, null=True, verbose_name='Файл')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Содержимое'
        verbose_name_plural = 'Содержимое'
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.content_type}"

class Quiz(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'
        ordering = ['order']

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name='Тест')
    text = models.TextField(verbose_name='Текст вопроса')
    correct_answer = models.CharField(max_length=200, verbose_name='Правильный ответ')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return self.text

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_results', verbose_name="Пользователь")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='results', verbose_name="Тест")
    answers = models.JSONField(verbose_name='Ответы')  # Формат: [{"question_id": X, "user_answer": "Y", "is_correct": true}, ...]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progress')
    completed_modules = models.ManyToManyField(Module, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"