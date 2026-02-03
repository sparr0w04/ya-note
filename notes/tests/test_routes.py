from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from notes.models import Note
from http import HTTPStatus

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей: автора и постороннего
        cls.author = User.objects.create_user(
            username='author', password='password'
        )
        cls.other_user = User.objects.create_user(
            username='other', password='password'
        )

        # Создаём заметку от автора
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )

    # 1. Главная страница доступна анонимному пользователю
    def test_home_page_anonymous(self):
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # 2. Страницы для аутентифицированного пользователя
    def test_authenticated_user_access(self):
        # Логинимся как автор
        self.client.login(username='author', password='password')

        urls = [
            reverse('notes:list'),
            reverse('notes:success'),
            reverse('notes:add'),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                f'Страница {url} недоступна авторизованному пользователю'
            )

    # 3. Страницы заметки доступны только автору
    def test_note_detail_edit_delete_author_only(self):
        urls = [
            reverse('notes:detail', args=(self.note.slug,)),
            reverse('notes:edit', args=(self.note.slug,)),
            reverse('notes:delete', args=(self.note.slug,)),
        ]

        # Анонимный пользователь → должен получить 404 или редирект на логин
        for url in urls:
            response = self.client.get(url)
            self.assertIn(
                response.status_code,
                [HTTPStatus.FOUND, HTTPStatus.NOT_FOUND],
                f'Анонимный пользователь видит {url}'
            )

        # Другой пользователь (не автор) → 404
        self.client.login(username='other', password='password')
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                HTTPStatus.NOT_FOUND,
                f'Другой пользователь видит {url}'
            )

        # Автор → 200
        self.client.login(username='author', password='password')
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                f'Автор не видит {url}'
            )

    # 4. Анонимный пользователь перенаправляется на логин
    def test_anonymous_redirect_to_login(self):
        urls = [
            reverse('notes:list'),
            reverse('notes:success'),
            reverse('notes:add'),
            reverse('notes:detail', args=(self.note.slug,)),
            reverse('notes:edit', args=(self.note.slug,)),
            reverse('notes:delete', args=(self.note.slug,)),
        ]

        login_url = reverse('users:login')

        for url in urls:
            response = self.client.get(url, follow=True)
            # Проверяем, что был редирект и конечный URL содержит login
            self.assertRedirects(
                response,
                f'{login_url}?next={url}',
                status_code=HTTPStatus.FOUND,
                target_status_code=HTTPStatus.OK
            )

    # 5. Страницы регистрации, входа и выхода доступны всем
    def test_public_pages_available(self):
        # 1. GET для signup и login → 200 OK
        public_get_urls = [
            reverse('users:signup'),
            reverse('users:login'),
        ]
        for url in public_get_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                f'GET {url} вернул {response.status_code}'
            )

        # 2. POST для logout → редирект (302)
        logout_url = reverse('users:logout')
        response = self.client.post(logout_url)
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,  # 302
            'POST для logout должен редиректить'
        )

        # 3. GET для logout → 405 Method Not Allowed
        response = self.client.get(logout_url)
        self.assertEqual(
            response.status_code,
            HTTPStatus.METHOD_NOT_ALLOWED,  # 405
            'GET для logout должен возвращать 405'
        )
