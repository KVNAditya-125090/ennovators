// The words of the app's shell (the account menu, the settings panel, the assistants and the sign-in window) in each language.
// A missing word falls back to English. These were written for the demo and should be reviewed by a native speaker of each language.
const en = {
  'settings.title': 'Settings',
  'settings.language': 'Language',
  'settings.language_help': 'Used across the app: the screens, the assistants and voice.',
  'settings.modes': 'How you talk to the assistants',
  'settings.modes_help': 'Choose one or more. Typing and reading are always available.',
  'mode.t2t': 'Text to text', 'mode.t2t_help': 'Type your question and read the answer.',
  'mode.t2s': 'Text to speech', 'mode.t2s_help': 'Type your question and hear the answer.',
  'mode.s2t': 'Speech to text', 'mode.s2t_help': 'Say your question and read the answer.',
  'mode.s2s': 'Speech to speech', 'mode.s2s_help': 'Say your question and hear the answer.',
  'settings.test_voice': 'Test voice',
  'settings.test_sentence': 'Hello, this is how I will sound.',
  'settings.unsupported_speak': 'This browser cannot read answers aloud. Try Chrome or Edge.',
  'settings.unsupported_listen': 'This browser cannot hear you. Try Chrome or Edge.',
  'settings.saved': 'Saved', 'settings.saving': 'Saving...', 'settings.done': 'Done',
  'menu.settings': 'Settings', 'menu.sign_out': 'Sign out', 'nav.search': 'Search',
  'assistant.title': 'Assistant', 'assistant.placeholder': 'Type your question', 'assistant.send': 'Send', 'assistant.thinking': 'Thinking...',
  'assistant.start': 'Ask a question to get started.', 'assistant.speak': 'Speak', 'assistant.listening': 'Listening...', 'assistant.stop': 'Stop',
  'signin.title': 'Sign in', 'signin.subtitle': 'to your Lakshmi workspace', 'signin.demo': 'Try a demo account'
};

const hi = {
  'settings.title': 'सेटिंग्स', 'settings.language': 'भाषा',
  'settings.language_help': 'यह भाषा पूरे ऐप में लागू होती है: स्क्रीन, असिस्टेंट और आवाज़।',
  'settings.modes': 'असिस्टेंट से बात करने का तरीका', 'settings.modes_help': 'एक या अधिक चुनें। लिखना और पढ़ना हमेशा उपलब्ध रहता है।',
  'mode.t2t': 'टेक्स्ट से टेक्स्ट', 'mode.t2t_help': 'सवाल लिखें और जवाब पढ़ें।',
  'mode.t2s': 'टेक्स्ट से आवाज़', 'mode.t2s_help': 'सवाल लिखें और जवाब सुनें।',
  'mode.s2t': 'आवाज़ से टेक्स्ट', 'mode.s2t_help': 'सवाल बोलें और जवाब पढ़ें।',
  'mode.s2s': 'आवाज़ से आवाज़', 'mode.s2s_help': 'सवाल बोलें और जवाब सुनें।',
  'settings.test_voice': 'आवाज़ जाँचें', 'settings.test_sentence': 'नमस्ते, मैं ऐसे बोलूँगा।',
  'settings.unsupported_speak': 'यह ब्राउज़र जवाब बोलकर नहीं सुना सकता। Chrome या Edge आज़माएँ।',
  'settings.unsupported_listen': 'यह ब्राउज़र बोली हुई बात नहीं समझ सकता। Chrome या Edge आज़माएँ।',
  'settings.saved': 'सहेजा गया', 'settings.saving': 'सहेज रहे हैं…', 'settings.done': 'ठीक है',
  'menu.settings': 'सेटिंग्स', 'menu.sign_out': 'साइन आउट', 'nav.search': 'खोजें',
  'assistant.title': 'सहायक', 'assistant.placeholder': 'अपना सवाल लिखें', 'assistant.send': 'भेजें', 'assistant.thinking': 'सोच रहा है…',
  'assistant.start': 'शुरू करने के लिए कोई सवाल पूछें।', 'assistant.speak': 'बोलें', 'assistant.listening': 'सुन रहा है…', 'assistant.stop': 'रोकें',
  'signin.title': 'साइन इन', 'signin.subtitle': 'अपने Lakshmi वर्कस्पेस में', 'signin.demo': 'डेमो अकाउंट आज़माएँ'
};

const te = {
  'settings.title': 'సెట్టింగ్స్', 'settings.language': 'భాష',
  'settings.language_help': 'ఈ భాష యాప్ అంతటా వర్తిస్తుంది: స్క్రీన్లు, అసిస్టెంట్లు మరియు వాయిస్.',
  'settings.modes': 'అసిస్టెంట్‌తో మాట్లాడే విధానం', 'settings.modes_help': 'ఒకటి లేదా ఎక్కువ ఎంచుకోండి. టైప్ చేయడం, చదవడం ఎల్లప్పుడూ అందుబాటులో ఉంటాయి.',
  'mode.t2t': 'టెక్స్ట్ నుండి టెక్స్ట్', 'mode.t2t_help': 'ప్రశ్న టైప్ చేసి, సమాధానం చదవండి.',
  'mode.t2s': 'టెక్స్ట్ నుండి వాయిస్', 'mode.t2s_help': 'ప్రశ్న టైప్ చేసి, సమాధానం వినండి.',
  'mode.s2t': 'వాయిస్ నుండి టెక్స్ట్', 'mode.s2t_help': 'ప్రశ్న చెప్పి, సమాధానం చదవండి.',
  'mode.s2s': 'వాయిస్ నుండి వాయిస్', 'mode.s2s_help': 'ప్రశ్న చెప్పి, సమాధానం వినండి.',
  'settings.test_voice': 'వాయిస్ పరీక్షించండి', 'settings.test_sentence': 'నమస్కారం, నేను ఇలా మాట్లాడతాను.',
  'settings.unsupported_speak': 'ఈ బ్రౌజర్ సమాధానాన్ని చదివి వినిపించలేదు. Chrome లేదా Edge ప్రయత్నించండి.',
  'settings.unsupported_listen': 'ఈ బ్రౌజర్ మీ మాటను గుర్తించలేదు. Chrome లేదా Edge ప్రయత్నించండి.',
  'settings.saved': 'సేవ్ అయింది', 'settings.saving': 'సేవ్ చేస్తోంది…', 'settings.done': 'సరే',
  'menu.settings': 'సెట్టింగ్స్', 'menu.sign_out': 'సైన్ అవుట్', 'nav.search': 'వెతకండి',
  'assistant.title': 'అసిస్టెంట్', 'assistant.placeholder': 'మీ ప్రశ్న టైప్ చేయండి', 'assistant.send': 'పంపండి', 'assistant.thinking': 'ఆలోచిస్తోంది…',
  'assistant.start': 'ప్రారంభించడానికి ఒక ప్రశ్న అడగండి.', 'assistant.speak': 'మాట్లాడండి', 'assistant.listening': 'వింటోంది…', 'assistant.stop': 'ఆపండి',
  'signin.title': 'సైన్ ఇన్', 'signin.subtitle': 'మీ Lakshmi వర్క్‌స్పేస్‌కు', 'signin.demo': 'డెమో ఖాతాను ప్రయత్నించండి'
};

const ta = {
  'settings.title': 'அமைப்புகள்', 'settings.language': 'மொழி',
  'settings.language_help': 'இந்த மொழி செயலி முழுவதும் பயன்படும்: திரைகள், உதவியாளர்கள் மற்றும் குரல்.',
  'settings.modes': 'உதவியாளருடன் பேசும் முறை', 'settings.modes_help': 'ஒன்று அல்லது பலவற்றைத் தேர்வு செய்யுங்கள். தட்டச்சு செய்வதும் படிப்பதும் எப்போதும் கிடைக்கும்.',
  'mode.t2t': 'உரையிலிருந்து உரை', 'mode.t2t_help': 'கேள்வியை தட்டச்சு செய்து பதிலைப் படியுங்கள்.',
  'mode.t2s': 'உரையிலிருந்து குரல்', 'mode.t2s_help': 'கேள்வியை தட்டச்சு செய்து பதிலைக் கேளுங்கள்.',
  'mode.s2t': 'குரலிலிருந்து உரை', 'mode.s2t_help': 'கேள்வியைப் பேசி பதிலைப் படியுங்கள்.',
  'mode.s2s': 'குரலிலிருந்து குரல்', 'mode.s2s_help': 'கேள்வியைப் பேசி பதிலைக் கேளுங்கள்.',
  'settings.test_voice': 'குரலைச் சோதிக்கவும்', 'settings.test_sentence': 'வணக்கம், நான் இப்படித்தான் பேசுவேன்.',
  'settings.unsupported_speak': 'இந்த உலாவியால் பதிலை வாசித்துக் காட்ட முடியாது. Chrome அல்லது Edge முயற்சிக்கவும்.',
  'settings.unsupported_listen': 'இந்த உலாவியால் உங்கள் பேச்சைப் புரிந்துகொள்ள முடியாது. Chrome அல்லது Edge முயற்சிக்கவும்.',
  'settings.saved': 'சேமிக்கப்பட்டது', 'settings.saving': 'சேமிக்கிறது…', 'settings.done': 'சரி',
  'menu.settings': 'அமைப்புகள்', 'menu.sign_out': 'வெளியேறு', 'nav.search': 'தேடு',
  'assistant.title': 'உதவியாளர்', 'assistant.placeholder': 'உங்கள் கேள்வியை தட்டச்சு செய்யுங்கள்', 'assistant.send': 'அனுப்பு', 'assistant.thinking': 'யோசிக்கிறது…',
  'assistant.start': 'தொடங்க ஒரு கேள்வி கேளுங்கள்.', 'assistant.speak': 'பேசுங்கள்', 'assistant.listening': 'கேட்கிறது…', 'assistant.stop': 'நிறுத்து',
  'signin.title': 'உள்நுழை', 'signin.subtitle': 'உங்கள் Lakshmi பணியிடத்திற்கு', 'signin.demo': 'டெமோ கணக்கை முயற்சிக்கவும்'
};

const kn = {
  'settings.title': 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', 'settings.language': 'ಭಾಷೆ',
  'settings.language_help': 'ಈ ಭಾಷೆ ಆ್ಯಪ್ ಪೂರ್ತಿ ಅನ್ವಯಿಸುತ್ತದೆ: ಪರದೆಗಳು, ಸಹಾಯಕರು ಮತ್ತು ಧ್ವನಿ.',
  'settings.modes': 'ಸಹಾಯಕರೊಂದಿಗೆ ಮಾತನಾಡುವ ವಿಧಾನ', 'settings.modes_help': 'ಒಂದು ಅಥವಾ ಹೆಚ್ಚು ಆಯ್ಕೆಮಾಡಿ. ಟೈಪ್ ಮಾಡುವುದು ಮತ್ತು ಓದುವುದು ಯಾವಾಗಲೂ ಲಭ್ಯ.',
  'mode.t2t': 'ಪಠ್ಯದಿಂದ ಪಠ್ಯ', 'mode.t2t_help': 'ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ, ಉತ್ತರವನ್ನು ಓದಿ.',
  'mode.t2s': 'ಪಠ್ಯದಿಂದ ಧ್ವನಿ', 'mode.t2s_help': 'ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ, ಉತ್ತರವನ್ನು ಕೇಳಿ.',
  'mode.s2t': 'ಧ್ವನಿಯಿಂದ ಪಠ್ಯ', 'mode.s2t_help': 'ಪ್ರಶ್ನೆಯನ್ನು ಹೇಳಿ, ಉತ್ತರವನ್ನು ಓದಿ.',
  'mode.s2s': 'ಧ್ವನಿಯಿಂದ ಧ್ವನಿ', 'mode.s2s_help': 'ಪ್ರಶ್ನೆಯನ್ನು ಹೇಳಿ, ಉತ್ತರವನ್ನು ಕೇಳಿ.',
  'settings.test_voice': 'ಧ್ವನಿ ಪರೀಕ್ಷಿಸಿ', 'settings.test_sentence': 'ನಮಸ್ಕಾರ, ನಾನು ಹೀಗೆ ಮಾತನಾಡುತ್ತೇನೆ.',
  'settings.unsupported_speak': 'ಈ ಬ್ರೌಸರ್ ಉತ್ತರವನ್ನು ಓದಿ ಹೇಳಲು ಸಾಧ್ಯವಿಲ್ಲ. Chrome ಅಥವಾ Edge ಪ್ರಯತ್ನಿಸಿ.',
  'settings.unsupported_listen': 'ಈ ಬ್ರೌಸರ್ ನಿಮ್ಮ ಮಾತನ್ನು ಗುರುತಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ. Chrome ಅಥವಾ Edge ಪ್ರಯತ್ನಿಸಿ.',
  'settings.saved': 'ಉಳಿಸಲಾಗಿದೆ', 'settings.saving': 'ಉಳಿಸುತ್ತಿದೆ…', 'settings.done': 'ಸರಿ',
  'menu.settings': 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', 'menu.sign_out': 'ಸೈನ್ ಔಟ್', 'nav.search': 'ಹುಡುಕಿ',
  'assistant.title': 'ಸಹಾಯಕ', 'assistant.placeholder': 'ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ', 'assistant.send': 'ಕಳುಹಿಸಿ', 'assistant.thinking': 'ಯೋಚಿಸುತ್ತಿದೆ…',
  'assistant.start': 'ಪ್ರಾರಂಭಿಸಲು ಒಂದು ಪ್ರಶ್ನೆ ಕೇಳಿ.', 'assistant.speak': 'ಮಾತನಾಡಿ', 'assistant.listening': 'ಕೇಳುತ್ತಿದೆ…', 'assistant.stop': 'ನಿಲ್ಲಿಸಿ',
  'signin.title': 'ಸೈನ್ ಇನ್', 'signin.subtitle': 'ನಿಮ್ಮ Lakshmi ವರ್ಕ್‌ಸ್ಪೇಸ್‌ಗೆ', 'signin.demo': 'ಡೆಮೊ ಖಾತೆಯನ್ನು ಪ್ರಯತ್ನಿಸಿ'
};

const mr = {
  'settings.title': 'सेटिंग्ज', 'settings.language': 'भाषा',
  'settings.language_help': 'ही भाषा संपूर्ण अ‍ॅपमध्ये लागू होते: स्क्रीन, सहाय्यक आणि आवाज.',
  'settings.modes': 'सहाय्यकाशी बोलण्याची पद्धत', 'settings.modes_help': 'एक किंवा अधिक निवडा. टाइप करणे आणि वाचणे नेहमी उपलब्ध असते.',
  'mode.t2t': 'मजकुरातून मजकूर', 'mode.t2t_help': 'प्रश्न टाइप करा आणि उत्तर वाचा.',
  'mode.t2s': 'मजकुरातून आवाज', 'mode.t2s_help': 'प्रश्न टाइप करा आणि उत्तर ऐका.',
  'mode.s2t': 'आवाजातून मजकूर', 'mode.s2t_help': 'प्रश्न बोला आणि उत्तर वाचा.',
  'mode.s2s': 'आवाजातून आवाज', 'mode.s2s_help': 'प्रश्न बोला आणि उत्तर ऐका.',
  'settings.test_voice': 'आवाज तपासा', 'settings.test_sentence': 'नमस्कार, मी असा बोलेन.',
  'settings.unsupported_speak': 'हा ब्राउझर उत्तर वाचून दाखवू शकत नाही. Chrome किंवा Edge वापरून पहा.',
  'settings.unsupported_listen': 'हा ब्राउझर तुमचे बोलणे ओळखू शकत नाही. Chrome किंवा Edge वापरून पहा.',
  'settings.saved': 'जतन केले', 'settings.saving': 'जतन करत आहे…', 'settings.done': 'ठीक आहे',
  'menu.settings': 'सेटिंग्ज', 'menu.sign_out': 'साइन आउट', 'nav.search': 'शोधा',
  'assistant.title': 'सहाय्यक', 'assistant.placeholder': 'तुमचा प्रश्न टाइप करा', 'assistant.send': 'पाठवा', 'assistant.thinking': 'विचार करत आहे…',
  'assistant.start': 'सुरू करण्यासाठी एक प्रश्न विचारा.', 'assistant.speak': 'बोला', 'assistant.listening': 'ऐकत आहे…', 'assistant.stop': 'थांबवा',
  'signin.title': 'साइन इन', 'signin.subtitle': 'तुमच्या Lakshmi वर्कस्पेसमध्ये', 'signin.demo': 'डेमो खाते वापरून पहा'
};

const bn = {
  'settings.title': 'সেটিংস', 'settings.language': 'ভাষা',
  'settings.language_help': 'এই ভাষা পুরো অ্যাপে প্রযোজ্য: স্ক্রিন, সহকারী এবং ভয়েস।',
  'settings.modes': 'সহকারীর সঙ্গে কথা বলার উপায়', 'settings.modes_help': 'এক বা একাধিক বেছে নিন। টাইপ করা ও পড়া সবসময় পাওয়া যায়।',
  'mode.t2t': 'লেখা থেকে লেখা', 'mode.t2t_help': 'প্রশ্ন টাইপ করুন, উত্তর পড়ুন।',
  'mode.t2s': 'লেখা থেকে কণ্ঠ', 'mode.t2s_help': 'প্রশ্ন টাইপ করুন, উত্তর শুনুন।',
  'mode.s2t': 'কণ্ঠ থেকে লেখা', 'mode.s2t_help': 'প্রশ্ন বলুন, উত্তর পড়ুন।',
  'mode.s2s': 'কণ্ঠ থেকে কণ্ঠ', 'mode.s2s_help': 'প্রশ্ন বলুন, উত্তর শুনুন।',
  'settings.test_voice': 'ভয়েস পরীক্ষা করুন', 'settings.test_sentence': 'নমস্কার, আমি এভাবে কথা বলব।',
  'settings.unsupported_speak': 'এই ব্রাউজার উত্তর পড়ে শোনাতে পারে না। Chrome বা Edge চেষ্টা করুন।',
  'settings.unsupported_listen': 'এই ব্রাউজার আপনার কথা বুঝতে পারে না। Chrome বা Edge চেষ্টা করুন।',
  'settings.saved': 'সংরক্ষিত', 'settings.saving': 'সংরক্ষণ হচ্ছে…', 'settings.done': 'ঠিক আছে',
  'menu.settings': 'সেটিংস', 'menu.sign_out': 'সাইন আউট', 'nav.search': 'খুঁজুন',
  'assistant.title': 'সহকারী', 'assistant.placeholder': 'আপনার প্রশ্ন টাইপ করুন', 'assistant.send': 'পাঠান', 'assistant.thinking': 'ভাবছে…',
  'assistant.start': 'শুরু করতে একটি প্রশ্ন করুন।', 'assistant.speak': 'বলুন', 'assistant.listening': 'শুনছে…', 'assistant.stop': 'থামান',
  'signin.title': 'সাইন ইন', 'signin.subtitle': 'আপনার Lakshmi ওয়ার্কস্পেসে', 'signin.demo': 'ডেমো অ্যাকাউন্ট চেষ্টা করুন'
};

const gu = {
  'settings.title': 'સેટિંગ્સ', 'settings.language': 'ભાષા',
  'settings.language_help': 'આ ભાષા આખી એપમાં લાગુ પડે છે: સ્ક્રીન, સહાયક અને અવાજ.',
  'settings.modes': 'સહાયક સાથે વાત કરવાની રીત', 'settings.modes_help': 'એક કે વધુ પસંદ કરો. ટાઇપ કરવું અને વાંચવું હંમેશાં ઉપલબ્ધ છે.',
  'mode.t2t': 'લખાણથી લખાણ', 'mode.t2t_help': 'પ્રશ્ન ટાઇપ કરો અને જવાબ વાંચો.',
  'mode.t2s': 'લખાણથી અવાજ', 'mode.t2s_help': 'પ્રશ્ન ટાઇપ કરો અને જવાબ સાંભળો.',
  'mode.s2t': 'અવાજથી લખાણ', 'mode.s2t_help': 'પ્રશ્ન બોલો અને જવાબ વાંચો.',
  'mode.s2s': 'અવાજથી અવાજ', 'mode.s2s_help': 'પ્રશ્ન બોલો અને જવાબ સાંભળો.',
  'settings.test_voice': 'અવાજ ચકાસો', 'settings.test_sentence': 'નમસ્તે, હું આ રીતે બોલીશ.',
  'settings.unsupported_speak': 'આ બ્રાઉઝર જવાબ વાંચી સંભળાવી શકતું નથી. Chrome અથવા Edge અજમાવો.',
  'settings.unsupported_listen': 'આ બ્રાઉઝર તમારી વાત ઓળખી શકતું નથી. Chrome અથવા Edge અજમાવો.',
  'settings.saved': 'સાચવ્યું', 'settings.saving': 'સાચવી રહ્યા છીએ…', 'settings.done': 'બરાબર',
  'menu.settings': 'સેટિંગ્સ', 'menu.sign_out': 'સાઇન આઉટ', 'nav.search': 'શોધો',
  'assistant.title': 'સહાયક', 'assistant.placeholder': 'તમારો પ્રશ્ન ટાઇપ કરો', 'assistant.send': 'મોકલો', 'assistant.thinking': 'વિચારી રહ્યું છે…',
  'assistant.start': 'શરૂ કરવા માટે એક પ્રશ્ન પૂછો.', 'assistant.speak': 'બોલો', 'assistant.listening': 'સાંભળી રહ્યું છે…', 'assistant.stop': 'રોકો',
  'signin.title': 'સાઇન ઇન', 'signin.subtitle': 'તમારા Lakshmi વર્કસ્પેસમાં', 'signin.demo': 'ડેમો ખાતું અજમાવો'
};

const ml = {
  'settings.title': 'ക്രമീകരണങ്ങൾ', 'settings.language': 'ഭാഷ',
  'settings.language_help': 'ഈ ഭാഷ ആപ്പിൽ മുഴുവൻ ബാധകമാണ്: സ്ക്രീനുകൾ, അസിസ്റ്റന്റുകൾ, ശബ്ദം.',
  'settings.modes': 'അസിസ്റ്റന്റുമായി സംസാരിക്കുന്ന രീതി', 'settings.modes_help': 'ഒന്നോ അതിലധികമോ തിരഞ്ഞെടുക്കുക. ടൈപ്പ് ചെയ്യലും വായിക്കലും എപ്പോഴും ലഭ്യമാണ്.',
  'mode.t2t': 'ടെക്സ്റ്റിൽ നിന്ന് ടെക്സ്റ്റ്', 'mode.t2t_help': 'ചോദ്യം ടൈപ്പ് ചെയ്ത് ഉത്തരം വായിക്കുക.',
  'mode.t2s': 'ടെക്സ്റ്റിൽ നിന്ന് ശബ്ദം', 'mode.t2s_help': 'ചോദ്യം ടൈപ്പ് ചെയ്ത് ഉത്തരം കേൾക്കുക.',
  'mode.s2t': 'ശബ്ദത്തിൽ നിന്ന് ടെക്സ്റ്റ്', 'mode.s2t_help': 'ചോദ്യം പറഞ്ഞ് ഉത്തരം വായിക്കുക.',
  'mode.s2s': 'ശബ്ദത്തിൽ നിന്ന് ശബ്ദം', 'mode.s2s_help': 'ചോദ്യം പറഞ്ഞ് ഉത്തരം കേൾക്കുക.',
  'settings.test_voice': 'ശബ്ദം പരിശോധിക്കുക', 'settings.test_sentence': 'നമസ്കാരം, ഞാൻ ഇങ്ങനെയാണ് സംസാരിക്കുക.',
  'settings.unsupported_speak': 'ഈ ബ്രൗസറിന് ഉത്തരം വായിച്ചു കേൾപ്പിക്കാൻ കഴിയില്ല. Chrome അല്ലെങ്കിൽ Edge പരീക്ഷിക്കുക.',
  'settings.unsupported_listen': 'ഈ ബ്രൗസറിന് നിങ്ങളുടെ സംസാരം തിരിച്ചറിയാൻ കഴിയില്ല. Chrome അല്ലെങ്കിൽ Edge പരീക്ഷിക്കുക.',
  'settings.saved': 'സംരക്ഷിച്ചു', 'settings.saving': 'സംരക്ഷിക്കുന്നു…', 'settings.done': 'ശരി',
  'menu.settings': 'ക്രമീകരണങ്ങൾ', 'menu.sign_out': 'സൈൻ ഔട്ട്', 'nav.search': 'തിരയുക',
  'assistant.title': 'അസിസ്റ്റന്റ്', 'assistant.placeholder': 'നിങ്ങളുടെ ചോദ്യം ടൈപ്പ് ചെയ്യുക', 'assistant.send': 'അയയ്ക്കുക', 'assistant.thinking': 'ചിന്തിക്കുന്നു…',
  'assistant.start': 'തുടങ്ങാൻ ഒരു ചോദ്യം ചോദിക്കുക.', 'assistant.speak': 'സംസാരിക്കുക', 'assistant.listening': 'കേൾക്കുന്നു…', 'assistant.stop': 'നിർത്തുക',
  'signin.title': 'സൈൻ ഇൻ', 'signin.subtitle': 'നിങ്ങളുടെ Lakshmi വർക്ക്‌സ്‌പേസിലേക്ക്', 'signin.demo': 'ഡെമോ അക്കൗണ്ട് പരീക്ഷിക്കുക'
};

export const STRINGS = { en, hi, te, ta, kn, mr, bn, gu, ml };

export const translate = (language, key) => STRINGS[language]?.[key] ?? en[key] ?? key;
