// Stage 1: serial "hello" over USB.
// Blinks the L LED and prints a numbered line every second.

unsigned long count = 0;  // lines sent since power-up

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);                    // USB serial (this board ignores the number; kept for habit)
  Serial.println("Sentinel Node booted");  // sent before anyone is listening
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.print("tick ");
  Serial.println(count);                   // e.g. "tick 7"
  count = count + 1;
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);
}
