# modules/brain.py
import google.generativeai as genai
import config
import cv2
from PIL import Image

class RobotBrain:
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.chat = self.model.start_chat(history=[])

    def ask(self, text):
        try:
            response = self.chat.send_message(text + "\n(Answer briefly in 2 sentences)")
            return response.text
        except:
            return "I am having trouble connecting."

    def see_and_describe(self, frame):
        try:
            # Convert OpenCV frame to Pillow Image
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            response = self.model.generate_content([pil_img, "Describe what you see briefly."])
            return response.text
        except Exception as e:
            return "I cannot see clearly right now."