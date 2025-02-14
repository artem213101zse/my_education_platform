from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    is_teacher = models.BooleanField(default=False, verbose_name='Является учителем')

    def __str__(self):
        return self.user.username

class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название курса')
    description = models.TextField(verbose_name='Описание курса')
    teacher = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='taught_courses', verbose_name='Автор курса')
    students = models.ManyToManyField(UserProfile, related_name='enrolled_courses', blank=True, verbose_name='Ученики курса')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')

    def __str__(self):
        return self.title

class Module(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название модуля')
    description = models.TextField(verbose_name='Описание модуля')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name='Курс к которому принадлежит модуль')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок модуля в списке')

    def __str__(self):
        return self.title


class Lesson(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class Content(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='contents', verbose_name='Модуль')
    content_type = models.CharField(max_length=50, choices=[('text', 'Text'), ('video', 'Video'), ('image', 'Image'), ('file', 'File')], verbose_name='Тип контента')
    text = models.TextField(blank=True, null=True, verbose_name='Текст')
    video_url = models.URLField(blank=True, null=True, verbose_name='Ссылка на видео')
    video_file = models.FileField(upload_to='content_videos/', blank=True, null=True, verbose_name='Прикрепить видео')  # Новое поле для видеофайлов
    image = models.ImageField(upload_to='content_images/', blank=True, null=True, verbose_name='Изображение')
    file = models.FileField(upload_to='content_files/', blank=True, null=True, verbose_name='Файл')

    def __str__(self):
        return f"{self.module.title} - {self.content_type}"



class Quiz(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name='Тест')
    text = models.TextField(verbose_name='Вопрос к тесту')

    def __str__(self):
        return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос')
    text = models.CharField(max_length=255, verbose_name='Вариант ответа')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')

    def __str__(self):
        return self.text


class QuizResult(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='quiz_results')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='results')
    score = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} - {self.quiz.title} - {self.score}"

class UserProgress(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progress')
    completed_modules = models.ManyToManyField(Module, blank=True)

    def __str__(self):
        return f"{self.user.user.username} - {self.course.title}"