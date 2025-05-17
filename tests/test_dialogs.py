import pytest
import dialogs

def test_set_response_and_destroy():
    # Simulate the private function for coverage
    response = [None]
    class DummyDialog:
        def destroy(self): self.destroyed = True
    dummy = DummyDialog()
    dialogs._set_response_and_destroy(dummy, response, True)
    assert response[0] is True

def test_get_password_and_destroy():
    response = [None]
    class DummyDialog:
        def destroy(self): self.destroyed = True
    dummy = DummyDialog()
    dialogs._get_password_and_destroy(dummy, response, 'pass')
    assert response[0] == 'pass'

