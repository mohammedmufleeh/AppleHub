from django import forms
from . models import Accounts

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder' : 'Enter Password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder' : 'Confirm Password'
    }))
    class Meta:
        model = Accounts
        fields =['first_name', 'last_name', 'email', 'phone_number', 'password', 'username']

    def clean(self):
        cleaned_data = super(RegistrationForm,self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password != confirm_password:
            raise forms.ValidationError("Password doesn't match")

    def __init__(self, *args, **kwargs):
        super(RegistrationForm,self).__init__(*args,**kwargs)

        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter First name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email address'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter phone number'
        self.fields['username'].widget.attrs['placeholder'] = 'Enter Username'

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'