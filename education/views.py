from .models import Course, Module, UserProfile, Content, UserProgress
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Quiz, Question, Answer, QuizResult
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from .forms import SignUpForm
from django.contrib.auth.decorators import user_passes_test

from django.db.models import Q


def course_list(request):
    query = request.GET.get('q')
    if query:
        courses = Course.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    else:
        courses = Course.objects.all()
    return render(request, 'education/course_list.html', {
        'courses': courses,


    })

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user_profile = None
    progress_percent = 0
    edit_mode = request.session.get('edit_mode', False)  # Получаем состояние режима редактирования

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        try:
            progress = UserProgress.objects.get(user=user_profile, course=course)
            completed_modules_count = progress.completed_modules.count()
            total_modules_count = course.modules.count()
            if total_modules_count > 0:
                progress_percent = (completed_modules_count / total_modules_count) * 100
        except UserProgress.DoesNotExist:
            pass  # Прогресс не найден, оставляем 0%

    # Получаем список студентов курса
    students = course.students.all()

    return render(request, 'education/course_detail.html', {
        'course': course,
        'user_profile': user_profile,
        # 'progress_percent': progress_percent,
        # 'students': students,
        'edit_mode': edit_mode,  # Передаем состояние режима редактирования
    })

def module_detail(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    contents = module.contents.all()
    quizzes = module.quizzes.all()  # Получаем все тесты модуля
    edit_mode = request.session.get('edit_mode', False)  # Получаем состояние режима редактирования
    return render(request, 'education/module_detail.html', {
        'module': module,
        'contents': contents,
        'quizzes': quizzes,  # Передаем тесты в контекст
        'edit_mode': edit_mode,  # Передаем состояние режима редактирования
    })


def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    if request.method == 'POST':
        # Обработка ответов
        score = 0
        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                selected_answer = Answer.objects.get(id=selected_answer_id)
                if selected_answer.is_correct:
                    score += 1

        # Сохранение результата
        user_profile = UserProfile.objects.get(user=request.user)
        QuizResult.objects.create(user=user_profile, quiz=quiz, score=score)

        messages.success(request, f'Your score: {score}/{questions.count()}')
        return redirect('module_detail', module_id=quiz.module.id)

    return render(request, 'education/quiz_detail.html', {'quiz': quiz, 'questions': questions})




@login_required
def quiz_results(request):
    user_profile = UserProfile.objects.get(user=request.user)
    results = user_profile.quiz_results.all()
    return render(request, 'education/quiz_results.html', {'results': results})

@login_required
def quiz_result_detail(request, result_id):
    result = get_object_or_404(QuizResult, id=result_id, user__user=request.user)
    questions = result.quiz.questions.all()
    return render(request, 'education/quiz_result_detail.html', {'result': result, 'questions': questions})




def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            is_teacher = form.cleaned_data.get('is_teacher')
            UserProfile.objects.create(user=user, is_teacher=is_teacher)
            login(request, user)
            return redirect('course_list')
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
    return render(request, 'education/login.html')


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile not in course.students.all():
        course.students.add(user_profile)
        messages.success(request, 'You have successfully enrolled in the course.')
    else:
        messages.warning(request, 'You are already enrolled in this course.')
    return redirect('course_detail', course_id=course.id)




def is_teacher(user):
    return user.userprofile.is_teacher

@login_required
@user_passes_test(is_teacher)
def create_course(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        teacher = request.user.userprofile
        course = Course.objects.create(title=title, description=description, teacher=teacher)
        messages.success(request, 'Course created successfully!')
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
        messages.success(request, 'Course updated successfully!')
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
        messages.success(request, 'Module added successfully!')
        return redirect('course_detail', course_id=course.id)
    return render(request, 'education/add_module.html', {'course': course})



@login_required
@user_passes_test(is_teacher)
def add_content(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__teacher=request.user.userprofile)
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        text = request.POST.get('text', '')
        video_url = request.POST.get('video_url', '')
        video_file = request.FILES.get('video_file')
        image = request.FILES.get('image')
        file = request.FILES.get('file')
        Content.objects.create(
            module=module,
            content_type=content_type,
            text=text,
            video_url=video_url,
            video_file=video_file,
            image=image,
            file=file
        )
        messages.success(request, 'Content added successfully!')
        return redirect('module_detail', module_id=module.id)
    return render(request, 'education/add_content.html', {'module': module})


@login_required
@user_passes_test(is_teacher)
def add_quiz(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__teacher=request.user.userprofile)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        quiz = Quiz.objects.create(title=title, description=description, module=module)
        messages.success(request, 'Quiz added successfully!')
        return redirect('module_detail', module_id=module.id)
    return render(request, 'education/add_quiz.html', {'module': module})


@login_required
@user_passes_test(is_teacher)
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, module__course__teacher=request.user.userprofile)
    if request.method == 'POST':
        text = request.POST.get('text')
        question = Question.objects.create(text=text, quiz=quiz)
        messages.success(request, 'Question added successfully!')
        return redirect('add_question', quiz_id=quiz.id)
    return render(request, 'education/add_question.html', {'quiz': quiz})

@login_required
@user_passes_test(is_teacher)
def add_answer(request, question_id):
    question = get_object_or_404(Question, id=question_id, quiz__module__course__teacher=request.user.userprofile)
    if request.method == 'POST':
        text = request.POST.get('text')
        is_correct = request.POST.get('is_correct', False) == 'on'
        Answer.objects.create(text=text, is_correct=is_correct, question=question)
        messages.success(request, 'Answer added successfully!')
        return redirect('add_answer', question_id=question.id)
    return render(request, 'education/add_answer.html', {'question': question})


@login_required
def complete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    user_profile = request.user.userprofile
    progress, created = UserProgress.objects.get_or_create(user=user_profile, course=module.course)
    progress.completed_modules.add(module)
    messages.success(request, f'Module "{module.title}" marked as completed!')
    return redirect('module_detail', module_id=module.id)

@login_required
@user_passes_test(is_teacher)
def edit_module(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__teacher=request.user.userprofile)
    if request.method == 'POST':
        module.title = request.POST.get('title')
        module.description = request.POST.get('description')
        module.order = request.POST.get('order', 0)
        module.save()
        messages.success(request, 'Module updated successfully!')
        return redirect('course_detail', course_id=module.course.id)
    return render(request, 'education/edit_module.html', {'module': module})

@login_required
@user_passes_test(is_teacher)
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__teacher=request.user.userprofile)
    course_id = module.course.id
    module.delete()
    messages.success(request, 'Module deleted successfully!')
    return redirect('course_detail', course_id=course_id)


@login_required
@user_passes_test(is_teacher)
def edit_content(request, content_id):
    content = get_object_or_404(Content, id=content_id, module__course__teacher=request.user.userprofile)
    if request.method == 'POST':
        content.content_type = request.POST.get('content_type')
        content.text = request.POST.get('text', '')
        content.video_url = request.POST.get('video_url', '')
        content.video_file = request.FILES.get('video_file', content.video_file)
        content.video_poster = request.FILES.get('video_poster', content.video_poster)
        content.image = request.FILES.get('image', content.image)
        content.file = request.FILES.get('file', content.file)
        content.save()
        messages.success(request, 'Content updated successfully!')
        return redirect('module_detail', module_id=content.module.id)
    return render(request, 'education/edit_content.html', {'content': content})

@login_required
@user_passes_test(is_teacher)
def delete_content(request, content_id):
    content = get_object_or_404(Content, id=content_id, module__course__teacher=request.user.userprofile)
    module_id = content.module.id
    content.delete()
    messages.success(request, 'Content deleted successfully!')
    return redirect('module_detail', module_id=module_id)

@login_required
@user_passes_test(is_teacher)
def toggle_edit_mode(request):
    edit_mode = request.session.get('edit_mode', False)
    request.session['edit_mode'] = not edit_mode
    return redirect(request.META.get('HTTP_REFERER', 'course_list'))