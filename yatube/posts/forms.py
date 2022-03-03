from django import forms

from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Название сообщества',
            'image': 'Изображение'
        }
        help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выбирите группу',
            'image': 'Выберите файл с изображением'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария'
        }
        help_texts = {
            'text': 'Введите текст комментария'
        }
