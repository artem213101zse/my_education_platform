from django.contrib import admin
from .models import Course, Module, Content, Quiz, Question, QuizResult

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'participant_count')
    list_filter = ('created_at', 'author')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Количество участников'

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course', 'order')
    search_fields = ('title', 'description')

class ContentAdmin(admin.ModelAdmin):
    list_display = ('module', 'content_type', 'title', 'preview_content')
    list_filter = ('content_type', 'module')
    search_fields = ('text', 'title', 'video_url')

    def preview_content(self, obj):
        if obj.content_type == 'text' and obj.text:
            return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
        elif obj.content_type == 'video' and obj.video_url:
            return obj.video_url[:50] + '...' if len(obj.video_url) > 50 else obj.video_url
        elif obj.content_type in ['image', 'file']:
            return f'{obj.content_type} прикреплён'
        return 'Нет предпросмотра'
    preview_content.short_description = 'Предпросмотр'

class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order')
    list_filter = ('module', 'order')
    search_fields = ('title',)

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'created_at')
    list_filter = ('quiz', 'created_at')
    search_fields = ('text', 'correct_answer')

class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'created_at', 'correct_answers_count')
    list_filter = ('quiz', 'user', 'created_at')
    search_fields = ('user__username',)

    def correct_answers_count(self, obj):
        return sum(1 for answer in obj.answers if answer.get('is_correct', False))
    correct_answers_count.short_description = 'Правильных ответов'

admin.site.register(Course, CourseAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuizResult, QuizResultAdmin)