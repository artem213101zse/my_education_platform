from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from education.models import Quiz, Question

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Имя")
    email = forms.EmailField(max_length=254, required=True, label="Email")
    is_teacher = forms.BooleanField(required=False, label="Зарегистрироваться как учитель")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password1', 'password2', 'is_teacher')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Пароли не совпадают.")
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    is_teacher = forms.BooleanField(required=False, label="Я учитель")

    class Meta:
        model = User
        fields = ('first_name', 'email', 'is_teacher')

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'correct_answer']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'correct_answer': forms.TextInput(attrs={'class': 'form-control'}),
        }