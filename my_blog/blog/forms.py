from django import forms
from .models import Comment


class EmailPostForm(forms.Form):
    name = forms.CharField(min_length=2, max_length=25)
    sender_email = forms.EmailField()
    recipient_email = forms.EmailField()
    comments = forms.CharField(required=False,
                               widget=forms.Textarea(attrs={'rows': 6, 'cols': 25, 'style': 'resize: none;'}))


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']


class SearchForm(forms.Form):
    query = forms.CharField(max_length=1024)
