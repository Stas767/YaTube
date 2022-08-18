from django.forms import ModelForm, Textarea

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'text': Textarea(attrs={'cols': 40, 'rows': 10}),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        exclude = ('author', 'post',)

# Егор, в слаке тебе писал, что убрал labels и help_texts в модели.
# В моделях добавил verbose_name и help_texts соответсвенно
