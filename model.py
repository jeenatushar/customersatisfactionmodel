import time
import cv2
import speech_recognition as sr
import threading
import json
from fer import FER
import csv
from tkinter import Tk, Label, Entry, Button, StringVar, messagebox

# Initialize global variables
running = False
cap = None
detector = None
last_log_time = None
log_interval = None

# Define emotion categories
def define_emotion(emotion, intensity):
    if emotion == "happy" and intensity > 0.7:
        return "Excellent"
    elif emotion == "happy":
        return "Good"
    elif emotion == "neutral" or (emotion == "surprise" and intensity < 0.6):
        return "Okay"
    elif emotion == "disgust" or (emotion == "angry" and intensity > 0.5):
        return "Poor"
    else:
        return "Needs Improvement"


def analyze_speech(text):
    negative_words = ["bad", "worst", "disappointed", "poor", "terrible"]
    positive_words = ["great", "good", "amazing", "excellent", "love"]
    
    if any(word in text.lower() for word in positive_words):
        return "Positive"
    elif any(word in text.lower() for word in negative_words):
        return "Negative"
    else:
        return "Neutral"

# Log feedback
def log_feedback(customer_id, dish_name, feedback, emotion, intensity, speech_sentiment, speech_text):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open('feedback_log.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(['Timestamp', 'Customer ID', 'Dish Name', 'Feedback', 'Emotion', 'Intensity', 'Speech Sentiment', 'Speech Text'])
        writer.writerow([timestamp, customer_id, dish_name, feedback, emotion, intensity, speech_sentiment, speech_text])
    print(f"Logged Feedback: {feedback}, Speech Sentiment: {speech_sentiment} for Customer ID: {customer_id} on Dish: {dish_name}")


def record_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening for feedback...")
        try:
            audio = recognizer.listen(source, timeout=5)
            speech_text = recognizer.recognize_google(audio)
            sentiment = analyze_speech(speech_text)
            print(f"Speech: {speech_text} | Sentiment: {sentiment}")
            return sentiment, speech_text
        except sr.UnknownValueError:
            return "Neutral", ""
        except sr.RequestError:
            return "Neutral", ""



def start_feedback():
    global running, cap, detector, last_log_time, log_interval

    dish_name = dish.get().strip()
    customer_id = customer.get().strip()

    if not dish_name or not customer_id:
        messagebox.showerror("Input Error", "Please enter both Customer ID and Dish Name.")
        return

    running = True
    cap = cv2.VideoCapture(0)
    detector = FER()
    last_log_time = time.time()
    log_interval = 20

    def detect_emotions():
        global running, last_log_time
        while running:
            ret, frame = cap.read()
            if not ret:
                break
            
            try:
                emotion_data = detector.detect_emotions(frame)
                if emotion_data:
                    emotions = emotion_data[0]['emotions']
                    emotion = max(emotions, key=emotions.get)
                    intensity = emotions[emotion]
                    feedback = define_emotion(emotion, intensity)
                    
                    speech_sentiment, speech_text = record_audio()
                    
                    current_time = time.time()
                    if current_time - last_log_time > log_interval:
                        log_feedback(customer_id, dish_name, feedback, emotion, intensity, speech_sentiment, speech_text)
                        last_log_time = current_time
                    
                    cv2.putText(frame, f'Customer ID: {customer_id}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f'Dish: {dish_name}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f'Emotion: {emotion} (Intensity: {intensity:.2f})', (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f'Speech Sentiment: {speech_sentiment}', (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f'Feedback: {feedback}', (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                cv2.imshow('Customer Feedback System', frame)

            except Exception as e:
                print(f"Error: {str(e)}")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    threading.Thread(target=detect_emotions, daemon=True).start()


root = Tk()
root.title("Customer Feedback System")
root.geometry("400x300")

Label(root, text="Customer Feedback System", font=("Arial", 16)).pack(pady=10)

Label(root, text="Customer ID:").pack(pady=5)
customer = StringVar()
Entry(root, textvariable=customer).pack(pady=5)

Label(root, text="Dish Name:").pack(pady=5)
dish = StringVar()
Entry(root, textvariable=dish).pack(pady=5)

Button(root, text="Start Feedback System", command=start_feedback, bg="green", fg="white").pack(pady=10)
Button(root, text="Stop Feedback System", command=stop_feedback, bg="red", fg="white").pack(pady=10)

root.mainloop()
