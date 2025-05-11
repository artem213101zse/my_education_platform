from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import Course, Module, Content, UserProgress, Quiz, Question, QuizResult
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from .forms import SignUpForm, UserProfileForm, QuizForm, QuestionForm
from django.db.models import Q
from itertools import chain
import json

def course_list(request):
    query = request.GET.get('q')
    courses = Course.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ) if query else Course.objects.all()

    my_courses = []
    all_courses = []
    progress_data = {}
    completed_modules_data = {}
    total_modules_data = {}
    last_course = None
    user = request.user
    if user.is_authenticated:
        for course in courses:
            total_modules = course.modules.count()
            if user in course.participants.all():
                my_courses.append(course)
                progress, created = UserProgress.objects.get_or_create(user=user, course=course)
                completed_modules = progress.completed_modules.count()
                progress_percent = (completed_modules / total_modules * 100) if total_modules > 0 else 0
                progress_data[course.id] = progress_percent
                completed_modules_data[course.id] = completed_modules
                total_modules_data[course.id] = total_modules
            else:
                all_courses.append(course)

        if my_courses:
            last_progress = UserProgress.objects.filter(user=user).order_by('-id').first()
            if last_progress:
                last_course = last_progress.course
                last_course.progress_percent = progress_data.get(last_course.id, 0)

    else:
        all_courses = list(courses)

    return render(request, 'education/course_list.html', {
        'my_courses': my_courses,
        'all_courses': all_courses,
        'progress_data': progress_data,
        'completed_modules_data': completed_modules_data,
        'total_modules_data': total_modules_data,
        'query': query,
        'last_course': last_course,
    })

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    progress_percent = 0
    students_progress = {}
    edit_mode = request.session.get('edit_mode', False)

    if request.user.is_authenticated:
        progress, created = UserProgress.objects.get_or_create(user=request.user, course=course)
        total_modules = course.modules.count()
        completed_modules = progress.completed_modules.count()
        progress_percent = (completed_modules / total_modules * 100) if total_modules > 0 else 0

        participants = course.participants.all()
        for student in participants:
            student_progress, _ = UserProgress.objects.get_or_create(user=student, course=course)
            student_completed = student_progress.completed_modules.count()
            students_progress[student.id] = {
                'completed_modules': student_completed,
                'total_modules': total_modules,
                'percent': (student_completed / total_modules * 100) if total_modules > 0 else 0
            }

    return render(request, 'education/course_detail.html', {
        'course': course,
        'user_profile': user_profile,
        'progress_percent': progress_percent,
        'participants': participants,
        'participants_progress': students_progress,
        'edit_mode': edit_mode,
    })

def is_teacher(user):
    return user.author

@login_required
def module_detail(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    contents = Content.objects.filter(module=module)
    quizzes = Quiz.objects.filter(module=module)

    try:
        user_profile = user=request.user
    except User.DoesNotExist:
        user_profile = None

    # Проверяем, прошёл ли пользователь тест
    quiz_results = {}
    for quiz in quizzes:
        result = QuizResult.objects.filter(user=user_profile, quiz=quiz).first()
        quiz_results[quiz.id] = result

    combined_items = sorted(
        chain(
            [{'type': 'content', 'order': content.order, 'content_type': content.content_type, 'title': content.title, 'text': content.text, 'video_url': content.video_url, 'video_file': content.video_file, 'image': content.image, 'file': content.file, 'id': content.id} for content in contents],
            [{'type': 'quiz', 'order': quiz.order, 'title': quiz.title, 'id': quiz.id, 'result': quiz_results.get(quiz.id)} for quiz in quizzes]
        ),
        key=lambda x: x['order']
    )

    return render(request, 'education/module_detail.html', {
        'module': module,
        'contents': contents,
        'quizzes': quizzes,
        'combined_items': combined_items,
        'edit_mode': request.session.get('edit_mode', False),
    })

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    total_questions = questions.count()
    user_profile = request.user
    # Проверяем, прошёл ли пользователь тест
    quiz_result = QuizResult.objects.filter(user=user_profile, quiz=quiz).first()
    if quiz_result:
        return redirect('quiz_results', quiz_id=quiz.id)
    # Разрешаем прохождение теста для всех пользователей
    if request.method == 'POST':
        if not questions:
            messages.error(request, 'В этом тесте нет вопросов.')
            return redirect('module_detail', module_id=quiz.module.id)
        # Собираем ответы
        answers = []
        for question in questions:
            user_answer = request.POST.get(f'answer_{question.id}', '').strip()
            is_correct = user_answer.lower() == question.correct_answer.lower()
            answers.append({
                'question_id': question.id,
                'user_answer': user_answer,
                'is_correct': is_correct,
            })

        # Сохраняем результат для всех пользователей
        QuizResult.objects.create(
            user=user_profile,
            quiz=quiz,
            answers=answers,
        )
        messages.success(request, 'Тест завершён! Посмотрите свои результаты.')
        return redirect('quiz_results', quiz_id=quiz.id)
    return render(request, 'education/quiz_detail.html', {
        'quiz': quiz,
        'questions': questions,
        'total_questions': total_questions,
        'is_teacher': user_profile == quiz.module.course.author,
    })


@login_required
def quiz_results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    user_profile = request.user
    questions = quiz.questions.all()
    total_questions = questions.count()

    if user_profile == quiz.module.course.author:
        # Для учителя: показываем результаты всех пользователей, включая самого учителя
        results = QuizResult.objects.filter(quiz=quiz)
        all_results = []
        for result in results:
            correct_answers = sum(1 for answer in result.answers if answer['is_correct'])
            all_results.append({
                'student': result.user,
                'correct': correct_answers,
                'total': total_questions,
                'percentage': (correct_answers / total_questions * 100) if total_questions > 0 else 0,
            })

        return render(request, 'education/quiz_results.html', {
            'quiz': quiz,
            'student_results': all_results,
            # Переименовываем student_results в all_results, так как теперь включаем всех
            'is_teacher': True,
        })
    else:
        # Для ученика: показываем его результат
        result = QuizResult.objects.filter(user=user_profile, quiz=quiz).first()
        if not result:
            messages.error(request, 'Вы ещё не прошли этот тест.')
            return redirect('quiz_detail', quiz_id=quiz.id)

        correct_answers = sum(1 for answer in result.answers if answer['is_correct'])
        progress = {
            'answers': result.answers,
            'correct': correct_answers,
            'total': total_questions,
            'percentage': (correct_answers / total_questions * 100) if total_questions > 0 else 0,
        }

        return render(request, 'education/quiz_results.html', {
            'quiz': quiz,
            'progress': progress,
            'questions': questions,
            'is_teacher': False,
        })

@login_required
def reset_quiz(request, quiz_id, user_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    user = get_object_or_404(User, id=user_id)
    if request.user != quiz.module.course.author:
        messages.error(request, 'Только автор курса может сбросить результаты.')
        return redirect('quiz_results', quiz_id=quiz.id)
    if request.method == 'POST':
        QuizResult.objects.filter(quiz=quiz, user=user).delete()
        messages.success(request, f'Результаты теста для {user.username} сброшены!')
    return redirect('quiz_results', quiz_id=quiz.id)

@login_required
def add_content(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__author=request.user)
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        title = request.POST.get('title', '').strip()

        if content_type == 'quiz':
            if not title:
                messages.error(request, 'Укажите название теста.')
                return redirect('add_content', module_id=module.id)
            quiz = Quiz.objects.create(title=title, module=module)
            messages.success(request, 'Тест добавлен успешно! Теперь добавьте вопросы.')
            return redirect('add_question', quiz_id=quiz.id)
        else:
            text = request.POST.get('text', '')
            video_url = request.POST.get('video_url', '')
            video_file = request.FILES.get('video_file')
            image = request.FILES.get('image')
            file = request.FILES.get('file')

            content = Content.objects.create(
                module=module,
                content_type=content_type,
                title=title,
                text=text,
                video_url=video_url,
                video_file=video_file,
                image=image,
                file=file
            )
            messages.success(request, f'Контент ({content_type}) добавлен успешно!')
            return redirect('module_detail', module_id=module.id)

    return render(request, 'education/add_content.html', {'module': module})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('course_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = SignUpForm()
    return render(request, 'education/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('course_list')
        else:
            messages.error(request, 'Неправильный логин или пароль.')
    return render(request, 'education/login.html')

@login_required
def enroll_course(request, course_id):
    user_profile = request.user
    course = get_object_or_404(Course, id=course_id)
    if user_profile not in course.participants.all():
        course.participants.add(user_profile)
        messages.success(request, 'Вы просоединились к курсу.')
    else:
        messages.warning(request, 'Вы уже находитесь на этом курсе.')
    return redirect('course_detail', course_id=course.id)

@login_required
def create_course(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        author = request.user
        course = Course.objects.create(title=title, description=description, author=author)
        messages.success(request, 'Курс создан!')
        return redirect('course_detail', course_id=course.id)
    return render(request, 'education/create_course.html')

@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, author=request.user)
    if request.method == 'POST':
        course.title = request.POST.get('title')
        course.description = request.POST.get('description')
        course.save()
        messages.success(request, 'Курс успешно обновлён!')
        return redirect('course_detail', course_id=course.id)
    return render(request, 'education/edit_course.html', {'course': course})

@login_required

def add_module(request, course_id):
    course = get_object_or_404(Course, id=course_id, author=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        Module.objects.create(title=title, description=description, course=course)
        messages.success(request, 'Модуль успешно создан!')
        return redirect('course_detail', course_id=course.id)
    return render(request, 'education/add_module.html', {'course': course})

@login_required
def complete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    user_profile = request.user
    progress, created = UserProgress.objects.get_or_create(user=user_profile, course=module.course)
    progress.completed_modules.add(module)
    messages.success(request, f'Модуль "{module.title}" завершен!')
    return redirect('module_detail', module_id=module.id)

@login_required
def edit_module(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__author=request.user)
    if request.method == 'POST':
        module.title = request.POST.get('title')
        module.description = request.POST.get('description')
        module.save()
        messages.success(request, 'Модуль обновлен!')
        return redirect('course_detail', course_id=module.course.id)
    return render(request, 'education/edit_module.html', {'module': module})

@login_required

def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__author=request.user)
    course_id = module.course.id
    module.delete()
    messages.success(request, 'Модуль удалён!')
    return redirect('course_detail', course_id=course_id)

@login_required

def edit_content(request, content_id):
    content = get_object_or_404(Content, id=content_id, module__course__author=request.user)
    if request.method == 'POST':
        content.content_type = request.POST.get('content_type')
        content.title = request.POST.get('title', '')
        content.text = request.POST.get('text', '')
        content.video_url = request.POST.get('video_url', '')
        content.video_file = request.FILES.get('video_file', content.video_file)
        content.image = request.FILES.get('image', content.image)
        content.file = request.FILES.get('file', content.file)
        content.save()
        messages.success(request, 'Содержимое обновлено!')
        return redirect('module_detail', module_id=content.module.id)
    return render(request, 'education/edit_content.html', {'content': content, 'module': content.module})


@login_required
def delete_content(request, content_id):
    content = get_object_or_404(Content, id=content_id, module__course__author=request.user)
    module_id = content.module.id
    content.delete()
    messages.success(request, 'Содержимое успешно удалено!')
    return redirect('module_detail', module_id=module_id)

@login_required

def toggle_edit_mode(request):
    edit_mode = request.session.get('edit_mode', False)
    request.session['edit_mode'] = not edit_mode
    return redirect(request.META.get('HTTP_REFERER', 'course_list'))

@login_required
def user_profile(request):
    user = request.user
    enrolled_courses = Course.objects.filter(participants=user)
    total_courses = enrolled_courses.count()
    total_progress = 0
    if total_courses > 0:
        for course in enrolled_courses:
            progress, _ = UserProgress.objects.get_or_create(user=user, course=course)
            total_modules = course.modules.count()
            completed_modules = progress.completed_modules.count()
            progress_percent = (completed_modules / total_modules * 100) if total_modules > 0 else 0
            total_progress += progress_percent
        average_progress = total_progress / total_courses
    else:
        average_progress = 0

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('user_profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'education/user_profile.html', {
        'form': form,
        'total_courses': total_courses,
        'average_progress': average_progress,
    })

@login_required

def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.user != quiz.module.course.author:
        return redirect('module_detail', module_id=quiz.module.id)

    module_id = quiz.module.id
    quiz.delete()
    return redirect('module_detail', module_id=module_id)

@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, module__course__author=request.user)

    if request.method == 'POST':
        question_count = 0
        while f'text_{question_count}' in request.POST:
            text = request.POST.get(f'text_{question_count}', '').strip()
            correct_answer = request.POST.get(f'correct_answer_{question_count}', '').strip()

            if text and correct_answer:
                Question.objects.create(
                    quiz=quiz,
                    text=text,
                    correct_answer=correct_answer,
                )
            question_count += 1

        if question_count == 0:
            messages.error(request, 'Необходимо добавить хотя бы один вопрос.')
        else:
            messages.success(request, 'Все вопросы добавлены успешно!')
        return redirect('add_question', quiz_id=quiz.id)

    return render(request, 'education/add_question.html', {'quiz': quiz})

@login_required

def quiz_user_answers(request, quiz_id, user_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, module__course__author=request.user)
    user = get_object_or_404(User, id=user_id)
    result = get_object_or_404(QuizResult, quiz=quiz, user=user)
    questions = quiz.questions.all()
    total_questions = questions.count()

    correct_answers = sum(1 for answer in result.answers if answer['is_correct'])
    progress = {
        'answers': result.answers,
        'correct': correct_answers,
        'total': total_questions,
        'percentage': (correct_answers / total_questions * 100) if total_questions > 0 else 0,
    }

    return render(request, 'education/quiz_user_answers.html', {
        'quiz': quiz,
        'user': user,
        'progress': progress,
        'questions': questions,
    })