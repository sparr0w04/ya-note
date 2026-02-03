import pytils.translit
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(
            username='author', password='password'
        )
        self.other_user = User.objects.create_user(
            username='other', password='password'
        )
        self.client = Client()

    def test_create_note_authenticated_vs_anonymous(self):
        self.client.login(username='author', password='password')
        url = reverse('notes:add')
        response = self.client.post(url, {
            'title': 'Новая заметка',
            'text': 'Текст',
            'slug': 'new-note'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Note.objects.filter(slug='new-note').exists())

        # Анонимный пользователь
        self.client.logout()
        response = self.client.post(url, {
            'title': 'Анонимная заметка',
            'text': 'Текст',
            'slug': 'anon-note'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.filter(slug='anon-note').exists())

    def test_unique_slug_constraint(self):
        self.client.login(username='author', password='password')
        url = reverse('notes:add')

        # Первая заметка
        self.client.post(url, {
            'title': 'Заметка 1',
            'text': 'Текст 1',
            'slug': 'unique-slug'
        })

        # Вторая заметка с тем же slug
        response = self.client.post(url, {
            'title': 'Заметка 2',
            'text': 'Текст 2',
            'slug': 'unique-slug'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertTrue(form.has_error('slug'))

        # Используем точный текст ошибки из формы
        self.assertIn(
            'unique-slug - такой slug уже существует, придумайте уникальное значение!',
            form.errors['slug']
        )

    def test_slugify_if_empty(self):
        self.client.login(username='author', password='password')
        url = reverse('notes:add')

        title = 'Заголовок с пробелами и спецсимволами!'
        expected_slug = pytils.translit.slugify(title)

        response = self.client.post(url, {
            'title': title,
            'text': 'Текст заметки',
        })

        self.assertEqual(response.status_code, 302)
        note = Note.objects.get(title=title)
        self.assertEqual(note.slug, expected_slug)

    def test_author_can_edit_delete_own_notes(self):
        self.client.login(username='author', password='password')
        note = Note.objects.create(
            title='Моя заметка',
            text='Текст',
            slug='my-note',
            author=self.author
        )

        # Редактирование
        url_edit = reverse('notes:edit', args=(note.slug,))
        response = self.client.post(url_edit, {
            'title': 'Изменённый заголовок',
            'text': 'Изменённый текст',
            'slug': note.slug
        })
        self.assertEqual(response.status_code, 302)
        note.refresh_from_db()
        self.assertEqual(note.title, 'Изменённый заголовок')

        # Удаление
        url_delete = reverse('notes:delete', args=(note.slug,))
        response = self.client.post(url_delete)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.filter(slug=note.slug).exists())

    def test_cannot_edit_delete_other_notes(self):
        self.client.login(username='other', password='password')
        note = Note.objects.create(
            title='Чужая заметка',
            text='Текст',
            slug='other-note',
            author=self.author
        )

        # Попытка редактирования
        url_edit = reverse('notes:edit', args=(note.slug,))
        response = self.client.post(url_edit, {
            'title': 'Попытка изменения',
            'text': 'Попытка текста',
            'slug': note.slug
        })
        self.assertEqual(response.status_code, 404)

        # Попытка удаления
        url_delete = reverse('notes:delete', args=(note.slug,))
        response = self.client.post(url_delete)
        self.assertEqual(response.status_code, 404)

        # Проверяем, что заметка не изменилась
        note.refresh_from_db()
        self.assertEqual(note.title, 'Чужая заметка')
        self.assertEqual(note.text, 'Текст')
