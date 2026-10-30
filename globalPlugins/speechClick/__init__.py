import time
import difflib
import os

import wx

import addonHandler
import config
import globalPluginHandler
import gui
import nvwave
import speech
import speechViewer
from gui import nvdaControls
from ui import message

addonHandler.initTranslation()

CONFIG_SECTION = 'speechClick'
BUILD_YEAR = 2026

DEFAULT_THRESHOLD = 50
MIN_THRESHOLD = 1
MAX_THRESHOLD = 5000

DEFAULT_RELEASE_TIME = 1000
MIN_RELEASE_TIME = 0
MAX_RELEASE_TIME = 30000

_SIMILARITY_RATIO = 0.85


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		confspec = {
			'enabled': 'boolean(default=true)',
			'threshold': f'integer(default={DEFAULT_THRESHOLD}, min={MIN_THRESHOLD}, max={MAX_THRESHOLD})',
			'releaseTime': f'integer(default={DEFAULT_RELEASE_TIME}, min={MIN_RELEASE_TIME}, max={MAX_RELEASE_TIME})',
		}
		config.conf.spec[CONFIG_SECTION] = confspec
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(SpeechClickSettingsPanel)

		self._lastText = ''
		self._lastTime = 0.0
		self._clickPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'click.wav')
		self._patch()

	def _patch(self):
		self._oldSpeak = speech.speech.speak
		speech.speech.speak = self._mySpeak

	def _mySpeak(self, sequence, *args, **kwargs):
		text = speechViewer.SPEECH_ITEM_SEPARATOR.join([x for x in sequence if isinstance(x, str)])
		if not text.strip():
			self._oldSpeak(sequence, *args, **kwargs)
			return

		if not config.conf[CONFIG_SECTION]['enabled']:
			self._speakAndRecord(text, sequence, *args, **kwargs)
			return

		now = time.time() * 1000
		timeSinceLast = now - self._lastTime
		threshold = config.conf[CONFIG_SECTION]['threshold']
		releaseTime = config.conf[CONFIG_SECTION]['releaseTime']

		if timeSinceLast < releaseTime and timeSinceLast < threshold and self._isSimilar(text, self._lastText):
			self._playClick()
			self._lastTime = now
			return

		self._speakAndRecord(text, sequence, *args, **kwargs)

	def _speakAndRecord(self, text, sequence, *args, **kwargs):
		self._lastText = text
		self._lastTime = time.time() * 1000
		self._oldSpeak(sequence, *args, **kwargs)

	def _isSimilar(self, a, b):
		if not a or not b:
			return False
		return difflib.SequenceMatcher(None, a, b).ratio() >= _SIMILARITY_RATIO

	def _playClick(self):
		if os.path.isfile(self._clickPath):
			nvwave.playWaveFile(self._clickPath)

	def script_toggle(self, gesture):
		current = config.conf[CONFIG_SECTION]['enabled']
		config.conf[CONFIG_SECTION]['enabled'] = not current
		if current:
			message(_('Speech click off'))
		else:
			message(_('Speech click on'))

	script_toggle.__doc__ = _('Toggles speech click on and off')
	script_toggle.category = _('Speech Click')

	def terminate(self, *args, **kwargs):
		super().terminate(*args, **kwargs)
		speech.speech.speak = self._oldSpeak
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(SpeechClickSettingsPanel)

	__gestures = {
		'kb:NVDA+control+shift+s': 'toggle',
	}


class SpeechClickSettingsPanel(gui.settingsDialogs.SettingsPanel):
	title = _('Speech Click')

	def makeSettings(self, settingsSizer):
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

		self.enabledCheckbox = helper.addItem(wx.CheckBox(self, label=_('&Enable speech click filter')))
		self.enabledCheckbox.SetValue(config.conf[CONFIG_SECTION]['enabled'])

		thresholdLabel = _('&Minimum time between repeated speech (ms):')
		self.thresholdEdit = helper.addLabeledControl(thresholdLabel, nvdaControls.SelectOnFocusSpinCtrl, min=MIN_THRESHOLD, max=MAX_THRESHOLD, initial=config.conf[CONFIG_SECTION]['threshold'])

		releaseLabel = _('&Speech resume delay after scrolling stops (ms):')
		self.releaseEdit = helper.addLabeledControl(releaseLabel, nvdaControls.SelectOnFocusSpinCtrl, min=MIN_RELEASE_TIME, max=MAX_RELEASE_TIME, initial=config.conf[CONFIG_SECTION]['releaseTime'])

	def onSave(self):
		config.conf[CONFIG_SECTION]['enabled'] = self.enabledCheckbox.GetValue()
		config.conf[CONFIG_SECTION]['threshold'] = self.thresholdEdit.GetValue()
		config.conf[CONFIG_SECTION]['releaseTime'] = self.releaseEdit.GetValue()
