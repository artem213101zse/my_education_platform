from django.contrib import admin
from .models import Course, Module, Content, Quiz, Question, UserProgress


class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('title', 'description')

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'description')

class ContentAdmin(admin.ModelAdmin):
    list_display = ('module', 'content_type',  'title', 'short_text')
    list_filter = ('content_type', 'module')
    search_fields = ('text',)

    def short_text(self, obj):
        return obj.text[:50] if obj.text else ''
    short_text.short_description = 'Предпросмотр текста'

class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'module')
    list_filter = ('module',)
    search_fields = ('title', 'description')

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz')
    list_filter = ('quiz',)
    search_fields = ('text',)

class AnswerAdmin(admin.ModelAdmin):
    list_filter = ('question', 'is_correct')
    search_fields = ('text',)

admin.site.register(Course, CourseAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)