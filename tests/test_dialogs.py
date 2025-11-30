import sys
import importlib
from unittest.mock import MagicMock, patch
import pytest
import allure

@pytest.fixture(scope="module")
def dialogs_module():
    modules = {
        'kivy': MagicMock(),
        'kivy.uix.popup': MagicMock(),
        'kivy.uix.label': MagicMock(),
        'kivy.uix.button': MagicMock(),
        'kivy.uix.boxlayout': MagicMock()
    }
    with patch.dict(sys.modules, modules):
        if 'dialogs' in sys.modules:
            import dialogs
            importlib.reload(dialogs)
        else:
            import dialogs
        yield dialogs

@allure.epic("UI Components")
@allure.suite("Dialogs")
class TestConfirmDialog:
    @allure.story("Interaction")
    def test_yes_callback(self, dialogs_module):
        user_callback = MagicMock()
        
        with patch('dialogs.Popup') as MockPopup, patch('dialogs.Button') as MockButton:
            dialogs_module.confirm_dialog(None, "Msg", user_callback)
            
            # Find the bind logic and trigger it
            btn_instance = MockButton.return_value
            # We assume the buttons were bound. Triggering arbitrary handlers found in bind
            for call in btn_instance.bind.call_args_list:
                handler = call.kwargs['on_release']
                handler(None) # Trigger
            
            # Assert dismiss was called
            MockPopup.return_value.dismiss.assert_called()