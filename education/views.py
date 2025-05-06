from django.template.defaultfilters import floatformat
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import Course, Module, UserProfile, Content, UserProgress, Quiz, Question, Answer
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from .forms import SignUpForm, UserProfileForm, QuizForm, QuestionForm
from django.db.models import Q
from itertools import chain
from django.http import JsonResponse
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

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        for course in courses:
            total_modules = course.modules.count()
            if user_profile in course.students.all():
                my_courses.append(course)
                progress, created = UserProgress.objects.get_or_create(user=user_profile, course=course)
                completed_modules = progress.completed_modules.count()
                progress_percent = (completed_modules / total_modules * 100) if total_modules > 0 else 0
                progress_data[course.id] = progress_percent
                completed_modules_data[course.id] = completed_modules
                total_modules_data[course.id] = total_modules
            else:
                all_courses.append(course)

        if my_courses:
            last_progress = UserProgress.objects.filter(user=user_profile).order_by('-id').first()
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
    user_profile = None
    progress_percent = 0
    students_progress = {}
    edit_mode = request.session.get('edit_mode', False)

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        progress, created = UserProgress.objects.get_or_create(user=user_profile, course=course)
        total_modules = course.modules.count()
        completed_modules = progress.completed_modules.count()
        progress_percent = (completed_modules / total_modules * 100) if total_modules > 0 else 0

        students = course.students.all()
        for student in students:
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
        'students': students,
        'students_progress': students_progress,
        'edit_mode': edit_mode,
    })

def is_teacher(user):
    return user.userprofile.is_teacher

@login_required
def module_detail(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    contents = Content.objects.filter(module=module)
    quizzes = Quiz.objects.filter(module=module)
    quiz_progress = {}
    student_progress = {}

    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    for quiz in quizzes:
        total_questions = quiz.questions.count()
        if user_profile:
            # Прогресс студента
            correct_answers = Answer.objects.filter(user=user_profile, question__quiz=quiz, is_correct=True).count()
            if total_questions > 0:
                percent = (correct_answers / total_questions) * 100
                quiz_progress[quiz.id] = {
                    'correct': correct_answers,
                    'total': total_questions,
                    'percent': percent
                }
            else:
                quiz_progress[quiz.id] = {'correct': 0, 'total': 0, 'percent': 0}

            # Прогресс всех студентов (для препода)
            if user_profile.is_teacher:
                students = module.course.students.all()
                student_progress[quiz.id] = {}
                total_percent = 0
                for student in students:
                    student_correct = Answer.objects.filter(user=student, question__quiz=quiz, is_correct=True).count()
                    if total_questions > 0:
                        student_percent = (student_correct / total_questions) * 100
                    else:
                        student_percent = 0
                    student_progress[quiz.id][student.id] = {
                        'username': student.user.username,
                        'correct': student_correct,
                        'total': total_questions,
                        'percent': student_percent
                    }
                    total_percent += student_percent
                quiz_progress[quiz.id]['average_percent'] = total_percent / len(students) if students else 0

    combined_items = sorted(
        chain(
            [{'type': 'content', 'order': content.order, 'content_type': content.content_type, 'title': content.title, 'text': content.text, 'video_url': content.video_url, 'video_file': content.video_file, 'image': content.image, 'file': content.file, 'id': content.id} for content in contents],
            [{'type': 'quiz', 'order': quiz.order, 'title': quiz.title, 'id': quiz.id, 'questions': quiz.questions} for quiz in quizzes]
        ),
        key=lambda x: x['order']
    )

    return render(request, 'education/module_detail.html', {
        'module': module,
        'contents': contents,
        'quizzes': quizzes,
        'combined_items': combined_items,
        'quiz_progress': quiz_progress,
        'student_progress': student_progress,
        'edit_mode': request.session.get('edit_mode', False),
    })

@login_required
def quiz_detail(request, quiz_id, q=0):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    total_questions = questions.count()

    user_profile = request.user.userprofile if request.user.is_authenticated else None

    # Определяем, находится ли учитель в режиме предпросмотра
    preview_mode = request.GET.get('preview', 'false') == 'true' and user_profile.is_teacher

    # Для студентов (или учителя в режиме предпросмотра): если нет вопросов, показываем сообщение
    if not user_profile.is_teacher or preview_mode:
        if not total_questions:
            messages.error(request, 'В этом тесте нет вопросов.')
            return redirect('module_detail', module_id=quiz.module.id)

    current_question_index = q
    if current_question_index < 0 or current_question_index >= total_questions:
        current_question_index = 0

    current_question = questions[current_question_index] if questions else None

    # Получаем список отвеченных вопросов (для студента или учителя в режиме предпросмотра)
    answered_questions = []
    if not preview_mode:
        answers = Answer.objects.filter(user=user_profile, question__quiz=quiz).select_related('question')
        answered_questions = [answer.question.id for answer in answers]

    # Формируем список индексов отвеченных вопросов
    answered_indices = []
    for idx, question in enumerate(questions):
        if question.id in answered_questions:
            answered_indices.append(idx)

    if request.method == 'POST':
        if not user_profile:
            messages.error(request, 'Вы должны быть авторизованы для ответа на тест.')
            return redirect('quiz_detail', quiz_id=quiz.id, q=0)

        answer_text = request.POST.get('answer', '')
        if not answer_text:
            messages.error(request, 'Пожалуйста, введите ответ.')
            return redirect('quiz_detail', quiz_id=quiz.id, q=current_question_index)

        # Сохраняем ответ только если это не предпросмотр
        if not preview_mode:
            Answer.objects.create(
                user=user_profile,
                question=current_question,
                answer_text=answer_text,
                is_correct=(answer_text.lower() == current_question.correct_answer.lower())
            )

        # Обновляем список отвеченных вопросов после сохранения ответа
        answered_questions.append(current_question.id)
        answered_indices = []
        for idx, question in enumerate(questions):
            if question.id in answered_questions:
                answered_indices.append(idx)

        # Проверяем, остались ли неотвеченные вопросы
        unanswered_indices = [i for i in range(total_questions) if i not in answered_indices]
        next_question_index = current_question_index + 1

        if unanswered_indices:
            # Если есть неотвеченные вопросы, перенаправляем на первый из них
            first_unanswered_index = min(unanswered_indices)
            if next_question_index != first_unanswered_index:
                messages.info(request, 'Есть неотвеченные вопросы. Переходим к первому из них.')
                redirect_url = f"{'quiz_detail'}?preview=true" if preview_mode else 'quiz_detail'
                return redirect(redirect_url, quiz_id=quiz.id, q=first_unanswered_index)
            elif next_question_index < total_questions:
                # Если следующий вопрос неотвеченный, переходим к нему
                messages.success(request, 'Ответ сохранён! Переходим к следующему вопросу.')
                redirect_url = f"{'quiz_detail'}?preview=true" if preview_mode else 'quiz_detail'
                return redirect(redirect_url, quiz_id=quiz.id, q=next_question_index)
            else:
                # Если дошли до конца, но есть неотвеченные, возвращаемся к первому неотвеченному
                messages.info(request, 'Есть неотвеченные вопросы. Переходим к первому из них.')
                redirect_url = f"{'quiz_detail'}?preview=true" if preview_mode else 'quiz_detail'
                return redirect(redirect_url, quiz_id=quiz.id, q=first_unanswered_index)
        else:
            # Если все вопросы отвечены, завершаем тест
            messages.success(request, 'Тест завершён! Посмотрите свои результаты.')
            redirect_url = f"{'quiz_results'}?preview=true" if preview_mode else 'quiz_results'
            return redirect(redirect_url, quiz_id=quiz.id)

    return render(request, 'education/quiz_detail.html', {
        'quiz': quiz,
        'questions': questions,
        'current_question': current_question,
        'current_question_index': current_question_index,
        'total_questions': total_questions,
        'preview_mode': preview_mode,
        'answered_indices': answered_indices,
    })

@login_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        for question in questions:
            answer_text = request.POST.get(f'answer_{question.id}', '').strip()
            if answer_text:
                is_correct = (answer_text.lower() == question.correct_answer.lower())
                Answer.objects.update_or_create(
                    user=user_profile,
                    question=question,
                    defaults={'answer_text': answer_text, 'is_correct': is_correct}
                )
        messages.success(request, 'Ответы сохранены!')
        return redirect('module_detail', module_id=quiz.module.id)

    return redirect('quiz_detail', quiz_id=quiz.id)

@login_required
@user_passes_test(is_teacher)
def reset_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, module__course__teacher=request.user.userprofile)
    if request.method == 'POST':
        Answer.objects.filter(question__quiz=quiz).delete()
        messages.success(request, 'Результаты теста сброшены!')
    return redirect('module_detail', module_id=quiz.module.id)

@login_required
@user_passes_test(is_teacher)
def add_content(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__teacher=request.user.userprofile)
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        print(f"Content type: {content_type}")  # Для отладки
        title = request.POST.get('title', '').strip()  # Получаем заголовок один раз для всех типов

        if content_type == 'quiz':
            if not title:
                messages.error(request, 'Укажите название теста.')
                return redirect('add_content', module_id=module.id)
            quiz = Quiz.objects.create(title=title, module=module)
            messages.success(request, 'Тест добавлен успешно! Теперь добавьте вопросы.')
            return redirect('add_question', quiz_id=quiz.id)  # Перенаправляем на добавление вопросов
        else:
            text = request.POST.get('text', '')
            video_url = request.POST.get('video_url', '')
            video_file = request.FILES.get('video_file')
            image = request.FILES.get('image')
            file = request.FILES.get('file')

            print(f"Text: {text}, Video URL: {video_url}, Video File: {video_file}, Image: {image}, File: {file}, Title: {title}")  # Для отладки

            content = Content.objects.create(
                module=module,
                content_type=content_type,
                title=title,  # Сохраняем заголовок для контента
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
            is_teacher = form.cleaned_data.get('is_teacher')
            UserProfile.objects.create(user=user, is_teacher=is_teacher)
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
    course = get_object_or_404(Course, id=course_id)
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile not in course.students.all():
        course.students.add(user_profile)
        messages.success(request, 'Вы просоединились к курсу.')
    else:
        messages.warning(request, 'Вы уже находитесь на этом курсе.')
    return redirect('course_detail', course_id=course.id)

@login_required
@user_passes_test(is_teacher)
def create_course(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        teacher = request.user.userprofile
        course = Course.objects.create(title=title, description=description, teacher=teacher)
        messages.success(request, 'Курс создан!')
        return redirect('course_detail', course_id=course.id)
    return render(request, 'education/create_course.html')

@login_required
@user_passes_test(is_teacher)
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user.userprofile)
    if request.method == 'POST':
        course.title = request.POST.get('title')
        course.description = request.POST.get('description')
        course.save()
        messages.success(request, 'Курс успешно обновлён!')
        return redirect('course_detail', course_id=course.id)
    return render(request, 'education/edit_course.html', {'course': course})

@login_required
@user_passes_test(is_teacher)
def add_module(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user.userprofile)
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
    user_profile = request.user.userprofile
    progress, created = UserProgress.objects.get_or_create(user=user_profile, course=module.course)
    progress.completed_modules.add(module)
    messages.success(request, f'Модуль "{module.title}" завершен!')
    return redirect('module_detail', module_id=module.id)

@login_required
@user_passes_test(is_teacher)
def edit_module(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__teacher=request.user.userprofile)
    if request.method == 'POST':
        module.title = request.POST.get('title')
        module.description = request.POST.get('description')
        module.save()
        messages.success(request, 'Модуль обновлен!')
        return redirect('course_detail', course_id=module.course.id)
    return render(request, 'education/edit_module.html', {'module': module})

@login_required
@user_passes_test(is_teacher)
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__teacher=request.user.userprofile)
    course_id = module.course.id
    module.delete()
    messages.success(request, 'Модуль удалён!')
    return redirect('course_detail', course_id=course_id)

@login_required
@user_passes_test(is_teacher)
def edit_content(request, content_id):
    content = get_object_or_404(Content, id=content_id, module__course__teacher=request.user.userprofile)
    if request.method == 'POST':
        content.content_type = request.POST.get('content_type')
        content.title = request.POST.get('title', '')  # Сохраняем заголовок
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
@user_passes_test(is_teacher)
def delete_content(request, content_id):
    content = get_object_or_404(Content, id=content_id, module__course__teacher=request.user.userprofile)
    module_id = content.module.id
    content.delete()
    messages.success(request, 'Содержимое успешно удалено!')
    return redirect('module_detail', module_id=module_id)

@login_required
@user_passes_test(is_teacher)
def toggle_edit_mode(request):
    edit_mode = request.session.get('edit_mode', False)
    request.session['edit_mode'] = not edit_mode
    return redirect(request.META.get('HTTP_REFERER', 'course_list'))

@login_required
def user_profile(request):
    user = request.user
    user_profile = user.userprofile
    enrolled_courses = Course.objects.filter(students=user_profile)
    total_courses = enrolled_courses.count()
    total_progress = 0
    if total_courses > 0:
        for course in enrolled_courses:
            progress, _ = UserProgress.objects.get_or_create(user=user_profile, course=course)
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
            user_profile.is_teacher = form.cleaned_data['is_teacher']
            user_profile.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('user_profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = UserProfileForm(instance=user, initial={'is_teacher': user_profile.is_teacher})

    return render(request, 'education/user_profile.html', {
        'form': form,
        'total_courses': total_courses,
        'average_progress': average_progress,
    })

@login_required
@user_passes_test(is_teacher)
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.user.userprofile != quiz.module.course.teacher:
        return redirect('module_detail', module_id=quiz.module.id)

    module_id = quiz.module.id
    quiz.delete()
    return redirect('module_detail', module_id=module_id)


@login_required
@user_passes_test(is_teacher)
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, module__course__teacher=request.user.userprofile)

    if request.method == 'POST':
        question_type = request.POST.get('question_type', 'text')
        text = request.POST.get('text', '').strip()

        # Получаем правильный ответ в зависимости от типа вопроса
        correct_answer = ''
        if question_type == 'text':
            correct_answer = request.POST.get('correct_answer_text', '').strip()
        else:
            correct_answer = request.POST.get('correct_answer_mc', '').strip()

        if not text or not correct_answer:
            messages.error(request, 'Укажите текст вопроса и правильный ответ.')
            return redirect('add_question', quiz_id=quiz.id)

        # Для множественного выбора собираем варианты ответа
        answer_options = None
        if question_type == 'multiple_choice':
            options = [
                request.POST.get('option1', '').strip(),
                request.POST.get('option2', '').strip(),
                request.POST.get('option3', '').strip(),
                request.POST.get('option4', '').strip(),
            ]
            # Фильтруем пустые варианты
            answer_options = [opt for opt in options if opt]
            if len(answer_options) < 2:
                messages.error(request, 'Укажите минимум 2 варианта ответа для множественного выбора.')
                return redirect('add_question', quiz_id=quiz.id)
            if correct_answer not in answer_options:
                messages.error(request, 'Правильный ответ должен быть одним из предложенных вариантов.')
                return redirect('add_question', quiz_id=quiz.id)

        Question.objects.create(
            quiz=quiz,
            question_type=question_type,
            text=text,
            correct_answer=correct_answer,
            answer_options=answer_options
        )
        messages.success(request, 'Вопрос добавлен успешно!')
        return redirect('quiz_detail', quiz_id=quiz.id, q=0)

    return render(request, 'education/add_question.html', {'quiz': quiz})

@login_required
def quiz_results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    user_profile = request.user.userprofile
    questions = quiz.questions.all()
    total_questions = questions.count()

    # Проверяем, находится ли учитель в режиме предпросмотра
    preview_mode = request.GET.get('preview', 'false') == 'true' and user_profile.is_teacher

    if user_profile.is_teacher and not preview_mode:
        # Для учителя: показываем результаты всех студентов
        answers = Answer.objects.filter(question__quiz=quiz).select_related('user', 'question')
        student_results = {}
        for answer in answers:
            student = answer.user
            if student not in student_results:
                student_results[student] = {
                    'correct': 0,
                    'total': 0,
                }
            student_results[student]['total'] += 1
            if answer.is_correct:
                student_results[student]['correct'] += 1

        # Формируем результаты для отображения
        results = [
            {
                'student': student,
                'correct': data['correct'],
                'total': data['total'],
                'percentage': (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0,
            }
            for student, data in student_results.items()
        ]

        return render(request, 'education/quiz_results.html', {
            'quiz': quiz,
            'results': results,
            'is_teacher': True,
            'preview_mode': preview_mode,
        })
    else:
        # Для студента или учителя в режиме предпросмотра: показываем его результаты
        answers = Answer.objects.filter(question__quiz=quiz, user=user_profile).select_related('question')
        correct_answers = answers.filter(is_correct=True).count()
        total_answered = answers.count()

        # Формируем прогресс
        progress = {
            'correct': correct_answers,
            'total_answered': total_answered,
            'total_questions': total_questions,
            'percentage': (correct_answers / total_questions * 100) if total_questions > 0 else 0,
            'answers': answers,  # Передаём все ответы для детального отображения
        }

        return render(request, 'education/quiz_results.html', {
            'quiz': quiz,
            'progress': progress,
            'is_teacher': user_profile.is_teacher,
            'preview_mode': preview_mode,
        })