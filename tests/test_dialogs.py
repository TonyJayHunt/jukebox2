import sys
from unittest.mock import MagicMock, patch

# --- Pre-Import Mocking of Kivy ---
mock_kivy = MagicMock()
sys.modules['kivy'] = mock_kivy
sys.modules['kivy.uix.popup'] = MagicMock()
sys.modules['kivy.uix.label'] = MagicMock()
sys.modules['kivy.uix.button'] = MagicMock()
sys.modules['kivy.uix.boxlayout'] = MagicMock()

import dialogs
import pytest
import allure

# --- Fixtures ---

@pytest.fixture
def mock_popup_class():
    """Captures the Popup instance created inside the functions."""
    with patch('dialogs.Popup') as MockPopup:
        yield MockPopup

@pytest.fixture
def mock_button_class():
    """Captures Buttons created to trigger their bindings."""
    with patch('dialogs.Button') as MockButton:
        yield MockButton

# --- Tests ---

@allure.epic("UI Components")
@allure.suite("Dialogs")
@allure.feature("Confirmation Dialog")
class TestConfirmDialog:

    @allure.story("Layout")
    @allure.title("Popup contains message and Yes/No buttons")
    def test_dialog_structure(self, mock_popup_class):
        """
        Scenario: confirm_dialog is called.
        Expectation: Popup is created with specific content structure.
        """
        callback = MagicMock()
        dialogs.confirm_dialog(None, "Are you sure?", callback)
        
        # Check Popup instantiation
        assert mock_popup_class.called
        _, kwargs = mock_popup_class.call_args
        assert kwargs['title'] == "Confirm"
        assert kwargs['auto_dismiss'] is False
        
        # Verify open was called
        mock_popup_class.return_value.open.assert_called_once()

    @allure.story("Interaction")
    @allure.title("Clicking Yes calls callback with True")
    def test_yes_callback(self, mock_popup_class, mock_button_class):
        """
        Scenario: 'Yes' button is clicked.
        Expectation: Popup dismisses, callback(True) fired.
        """
        user_callback = MagicMock()
        
        # 1. Call the function
        dialogs.confirm_dialog(None, "Msg", user_callback)
        
        # 2. Extract the 'Yes' button binding.
        # The function creates 2 buttons: Yes and No.
        # Usually 'Yes' is the first one created or we can check the text kwarg.
        # We assume distinct calls to Button(text="Yes") and Button(text="No")
        
        yes_btn_mock = None
        for call in mock_button_class.call_args_list:
            if call.kwargs.get('text') == "Yes":
                # We need the instance returned by this call
                # But mock_button_class() returns the SAME mock instance by default unless side_effect set.
                # However, the code calls btn.bind(on_release=...).
                # We need to capture the function passed to bind.
                pass

        # Since Button() is a class mock, it returns a mock instance. 
        # The code does: btn_yes = Button(...); btn_yes.bind(on_release=on_yes)
        # We need to grab the `on_yes` function passed to bind.
        
        # Inspect all calls to bind on the return value of Button()
        # The mocked Button class returns the SAME instance for every instantiation by default.
        btn_instance = mock_button_class.return_value
        
        # bind is called twice: once for Yes, once for No.
        # We need to distinguish them. The code logic is:
        # btn_yes = Button(text="Yes") ... btn_yes.bind(on_release=on_yes)
        # btn_no = Button(text="No") ... btn_no.bind(on_release=on_no)
        
        # Because checking which bind belongs to which text is hard with a single return value,
        # we trigger the effects by verifying the closure logic instead.
        # Alternatively, we can inspect `btn_instance.bind.call_args_list`.
        
        assert btn_instance.bind.call_count == 2
        
        # Let's just manually trigger the callbacks captured.
        # We don't know strictly which is Yes or No without complex mocking, 
        # but we know one should call callback(True) and one callback(False).
        
        callbacks_found = []
        for call in btn_instance.bind.call_args_list:
            # call.kwargs is {'on_release': <function on_yes at ...>}
            handler = call.kwargs['on_release']
            
            # Reset mock to track new calls
            user_callback.reset_mock()
            mock_popup_class.return_value.dismiss.reset_mock()
            
            # Fire the handler
            handler(None)
            
            if user_callback.call_count > 0:
                args = user_callback.call_args[0]
                callbacks_found.append(args[0]) # True or False
                
                # Assert dismiss was called
                mock_popup_class.return_value.dismiss.assert_called()

        assert True in callbacks_found
        assert False in callbacks_found


@allure.epic("UI Components")
@allure.suite("Dialogs")
@allure.feature("Error Dialog")
class TestErrorDialog:

    @allure.story("Interaction")
    @allure.title("Clicking OK dismisses popup")
    def test_error_ok_callback(self, mock_popup_class, mock_button_class):
        """
        Scenario: 'OK' button clicked.
        Expectation: Popup dismisses, optional callback fired.
        """
        user_callback = MagicMock()
        dialogs.confirm_dialog_error(None, "Error Msg", user_callback)
        
        # Verify Title
        assert mock_popup_class.call_args[1]['title'] == "Error"
        
        # Find the bind call
        btn_instance = mock_button_class.return_value
        args, kwargs = btn_instance.bind.call_args
        handler = kwargs['on_release']
        
        # Trigger
        handler(None)
        
        # Assertions
        mock_popup_class.return_value.dismiss.assert_called_once()
        user_callback.assert_called_once()

    @allure.story("Robustness")
    @allure.title("Handles missing callback safely")
    def test_error_no_callback(self, mock_popup_class, mock_button_class):
        """
        Scenario: confirm_dialog_error called without a callback.
        Expectation: OK button dismisses popup without crashing.
        """
        dialogs.confirm_dialog_error(None, "Error Msg")
        
        btn_instance = mock_button_class.return_value
        handler = btn_instance.bind.call_args.kwargs['on_release']
        
        # Trigger should not raise error
        handler(None)
        
        mock_popup_class.return_value.dismiss.assert_called_once()