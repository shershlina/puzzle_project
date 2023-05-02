from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста *',
            'group': 'Группа',
            'image': 'Изображение',
        }
        help_texts = {
            'text': 'Напишите здесь что-нибудь интересное',
            'group': 'Можете выбрать группу для своего поста',
            'image': 'Можете приложить фото, иллюстрацию или мем',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = {'text'}
        labels = {
            'text': 'Текст комментария'
        }
        help_texts = {
            'text': 'Оставьте здесь свой комментарий'
        }
