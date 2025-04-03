from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('course/create/', views.create_course, name='create_course'),
    path('course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('course/<int:course_id>/add_module/', views.add_module, name='add_module'),
    path('module/<int:module_id>/add_content/', views.add_content, name='add_content'),
    path('module/<int:module_id>/add_quiz/', views.add_quiz, name='add_quiz'),
    path('quiz/<int:quiz_id>/add_question/', views.add_question, name='add_question'),
    path('question/<int:question_id>/add_answer/', views.add_answer, name='add_answer'),
    path('module/<int:module_id>/complete/', views.complete_module, name='complete_module'),
    path('module/<int:module_id>/edit/', views.edit_module, name='edit_module'),
    path('module/<int:module_id>/delete/', views.delete_module, name='delete_module'),
    path('content/<int:content_id>/edit/', views.edit_content, name='edit_content'),
    path('content/<int:content_id>/delete/', views.delete_content, name='delete_content'),
    path('toggle-edit-mode/', views.toggle_edit_mode, name='toggle_edit_mode'),
]