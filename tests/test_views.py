import pytest
import os

from app import app

class TestViewsNoUser:
    def test_login_page(self):
        response = app.test_client().get('/login')

        assert response.status_code == 200
        assert "email" in response.data.decode("utf-8")
        assert b"Login" in response.data
        assert b"Your Email" in response.data
        assert b"Your Password" in response.data

        assert b"Calendar" not in response.data
        assert b"Settings" not in response.data
        assert b"Logout" not in response.data

    @pytest.mark.parametrize(
            'path',
            ["calendar", "settings", "logout", "index", "", 
             "day", "day/20230101", "edit/20230101", "edit",
             "new", "new/20230101", "dummy_not_existing_page"]
    )
    def test_blocked_pages(self, path):
        response = app.test_client().get(f"/{path}", follow_redirects=True)

        assert response.status_code == 200
        assert response.request.path == '/login'
        assert len(response.history) > 0


class TestViewsNewUser:
    @pytest.fixture(autouse=True)
    def client_logged_in(self):
        client = app.test_client()
        response = client.post('/login', data={
            'email': 'dummy@dummy.com',
            'password': 'dummy'
            }
        )
        return client

    @pytest.mark.parametrize(
            'path',
            ["login", "signup"]
    )
    def test_pages_to_redirect(self, client_logged_in, path):
        response = client_logged_in.get(path, follow_redirects=True)

        assert response.status_code == 200
        assert response.request.path == "/index"

    @pytest.mark.parametrize(
            'path',
            ["/calendar/202401", "/settings", "/index", "/"]
    )
    def test_pages_to_render(self, client_logged_in, path):
        response = client_logged_in.get(path, follow_redirects=True)

        assert response.status_code == 200
        assert response.request.path == path
        assert len(response.history) == 0

    @pytest.mark.parametrize(
            'path,target',
            # [("/day/20000101", "/past",), ("/edit/20000101", "/past",), 
            [ ("/day/30000101", "/future"), ("/edit/30000101", "/future"),
             ("/logout", "/login")]
    )
    def test_pages_to_redirect(self, client_logged_in, path, target):
        response = client_logged_in.get(path, follow_redirects=True)

        assert response.status_code == 200
        assert response.request.path == target
        assert len(response.history) == 1
    
