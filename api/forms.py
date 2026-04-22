from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(label='用户名或邮箱', max_length=150)
    password = forms.CharField(label='密码', widget=forms.PasswordInput)
    remember_me = forms.BooleanField(label='记住登录状态', required=False)


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='企业邮箱', max_length=254)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('该邮箱已注册')
        return email
