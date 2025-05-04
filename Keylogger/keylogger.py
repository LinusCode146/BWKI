import json
import time
import pygame
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://linusschulze42:va3zxFuIx7fR87y5@logdata.atbyrto.mongodb.net/?retryWrites=true&w=majority&appName=LogData"
DATABASE_NAME = "LoggerData"
COLLECTION_NAME = "JsonTokens"
LOCAL_FILE = "keystrokes.json"

class KeyLoggerPygame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((600, 300))
        pygame.display.set_caption('Keylogger - Setup')

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)

        self.name_input = ""
        self.duration_input = ""
        self.input_active = "name"  # or "duration"
        self.running = True
        self.logging_active = False

        self.start_time = None
        self.duration_seconds = 0
        self.keystrokes = []
        self.last_time = None

    def draw_input_screen(self):
        self.screen.fill((30, 30, 30))

        # Name input
        name_label = self.font.render("Name (FIRST LAST, UPPERCASE):", True, (255, 255, 255))
        self.screen.blit(name_label, (50, 20))
        pygame.draw.rect(self.screen, (255, 255, 255), (50, 50, 500, 32), 2)
        name_surface = self.font.render(self.name_input, True, (255, 255, 255))
        self.screen.blit(name_surface, (55, 55))

        # Duration input
        duration_label = self.font.render("Duration (minutes):", True, (255, 255, 255))
        self.screen.blit(duration_label, (50, 100))
        pygame.draw.rect(self.screen, (255, 255, 255), (50, 130, 500, 32), 2)
        duration_surface = self.font.render(self.duration_input, True, (255, 255, 255))
        self.screen.blit(duration_surface, (55, 135))

        # Start button
        pygame.draw.rect(self.screen, (0, 200, 0), (200, 200, 200, 40))
        button_text = self.font.render("START", True, (0, 0, 0))
        self.screen.blit(button_text, (265, 210))

    def draw_logging_screen(self):
        self.screen.fill((0, 0, 0))
        logging_text = self.font.render("Logging... Press ESC to stop", True, (255, 255, 255))
        self.screen.blit(logging_text, (150, 130))

    def start(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if 200 <= x <= 400 and 200 <= y <= 240 and not self.logging_active:
                        if self.name_input and self.duration_input.isdigit():
                            self.duration_seconds = int(self.duration_input) * 60
                            self.start_time = time.time()
                            self.keystrokes = [{self.name_input.strip().upper(): []}]
                            self.logging_active = True
                            pygame.display.set_caption('Keylogger - Logging')
                        else:
                            print("Invalid input.")

                    elif 50 <= x <= 550 and 50 <= y <= 82:
                        self.input_active = "name"
                    elif 50 <= x <= 550 and 130 <= y <= 162:
                        self.input_active = "duration"

                elif event.type == pygame.KEYDOWN:
                    if self.logging_active:
                        self.handle_key(event.key)
                    else:
                        if event.key == pygame.K_TAB:
                            self.input_active = "duration" if self.input_active == "name" else "name"
                        elif event.key == pygame.K_BACKSPACE:
                            if self.input_active == "name":
                                self.name_input = self.name_input[:-1]
                            else:
                                self.duration_input = self.duration_input[:-1]
                        else:
                            char = event.unicode
                            if self.input_active == "name":
                                self.name_input += char.upper()
                            elif self.input_active == "duration" and char.isdigit():
                                self.duration_input += char

            # Auto-stop after time
            if self.logging_active and time.time() - self.start_time >= self.duration_seconds:
                self.running = False
                pygame.quit()
                self.save_locally()
                self.push_to_mongo()
                return

            # Drawing
            if self.logging_active:
                self.draw_logging_screen()
            else:
                self.draw_input_screen()

            pygame.display.flip()
            self.clock.tick(60)

    def handle_key(self, key):
        now_monotonic = time.monotonic()
        time_since_last = (now_monotonic - self.last_time) * 1000 if self.last_time else None
        self.last_time = now_monotonic

        keystroke = {
            "key": pygame.key.name(key),
            "time_since_last": time_since_last,
        }

        for user_entry in self.keystrokes:
            if self.name_input.strip().upper() in user_entry:
                user_entry[self.name_input.strip().upper()].append(keystroke)

        if key == pygame.K_ESCAPE:
            self.running = False
            pygame.quit()
            self.save_locally()
            self.push_to_mongo()

    def save_locally(self):
        try:
            with open(LOCAL_FILE, "w") as f:
                json.dump(self.keystrokes, f, indent=4)
            print("Saved locally.")
        except Exception as e:
            print(f"Failed to save: {e}")

    def push_to_mongo(self):
        try:
            client = MongoClient(MONGO_URI)
            db = client[DATABASE_NAME]
            collection = db[COLLECTION_NAME]
            if self.keystrokes:
                collection.insert_many(self.keystrokes)
            print("Uploaded to MongoDB.")
        except Exception as e:
            print(f"MongoDB error: {e}")


if __name__ == "__main__":
    logger = KeyLoggerPygame()
    logger.start()
