// Stage 1: read the potentiometer on A0 and send it over USB serial.
// Temporary human-readable format, one line every 200 ms:
//   tick <n> a0 <0-1023>

const int SENSOR_PIN = A0;   // potentiometer wiper (analogRead sets up the pin itself)

unsigned long count = 0;     // lines sent since power-up
bool ledOn = false;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);      // USB serial (this board ignores the number; kept for habit)
}

void loop() {
  int reading = analogRead(SENSOR_PIN);   // 10-bit: 0 to 1023

  Serial.print("tick ");
  Serial.print(count);
  Serial.print(" a0 ");
  Serial.println(reading);                // e.g. "tick 12 a0 517"
  count = count + 1;

  ledOn = !ledOn;                         // blink so we can see the loop running
  digitalWrite(LED_BUILTIN, ledOn ? HIGH : LOW);

  delay(200);
}
