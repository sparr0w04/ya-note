from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей
        cls.author = User.objects.create_user(
            username='author', password='password'
        )
        cls.other_user = User.objects.create_user(
            username='other', password='password'
        )

        # Заметки автора
        cls.note1 = Note.objects.create(
            title='Заметка 1',
            text='Текст 1',
            slug='note-1',
            author=cls.author
        )
        cls.note2 = Note.objects.create(
            title='Заметка 2',
            text='Текст 2',
            slug='note-2',
            author=cls.author
        )

        # Заметка другого пользователя
        cls.other_note = Note.objects.create(
            title='Чужая заметка',
            text='Чужой текст',
            slug='other-note',
            author=cls.other_user
        )

    def test_note_in_list_page(self):
        """Проверяет, что заметка передаётся в object_list на странице списка."""
        self.client.login(username='author', password='password')
        url = reverse('notes:list')
        response = self.client.get(url)

        # Проверяем, что в контексте есть object_list
        self.assertIn('object_list', response.context)
        object_list = response.context['object_list']

        # Проверяем, что заметки автора есть в списке
        self.assertIn(self.note1, object_list)
        self.assertIn(self.note2, object_list)

    def test_only_author_notes_in_list(self):
        """Проверяет, что в списке только заметки текущего пользователя."""
        self.client.login(username='author', password='password')
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']

        # Автор не должен видеть чужую заметку
        self.assertNotIn(self.other_note, object_list)

    def test_forms_in_create_edit_pages(self):
        """Проверяет, что на страницах создания/редактирования передаётся форма."""
        self.client.login(username='author', password='password')

        # Страница создания
        url_add = reverse('notes:add')
        response_add = self.client.get(url_add)
        self.assertIn('form', response_add.context)

        # Страница редактирования
        url_edit = reverse('notes:edit', args=(self.note1.slug,))
        response_edit = self.client.get(url_edit)
        self.assertIn('form', response_edit.context)
