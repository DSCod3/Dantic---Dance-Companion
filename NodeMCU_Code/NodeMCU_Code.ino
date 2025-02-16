#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <Servo.h> // Include the Servo library  

// Define Servo objects
Servo s1;
Servo s2;

// Define LED Pins for two separate LED setups
#define LED_PIN1 D6 // Red LED (Set 1)
#define LED_PIN2 D7 // Green LED (Set 1)
#define LED_PIN3 D8 // Blue LED (Set 1)

#define LED_PIN4 D0 // Red LED (Set 2)
#define LED_PIN5 D1 // Green LED (Set 2)
#define LED_PIN6 D2 // Blue LED (Set 2)

// WiFi Credentials (Change These)
const char *ssid = "Jim"; // WiFi SSID
const char *password = "12345678"; // WiFi Password

// Create an instance of ESP8266 Web Server
ESP8266WebServer server(80);

// Variables to store received intensity values
int intensity1 = 0, intensity2 = 0, intensity3 = 0, intensity4 = 0;

// HTML Webpage stored in Flash Memory (PROGMEM)
const char HTML_PAGE[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; }
        .container { margin-top: 50px; }
        .button { padding: 10px 20px; font-size: 18px; cursor: pointer; margin: 10px; border: none; background-color: blue; color: white; }
        input { padding: 5px; font-size: 16px; width: 60px; }
    </style>
    <script>
        function sendValues() {
            var intensity1 = document.getElementById("intensity1").value;
            var intensity2 = document.getElementById("intensity2").value;
            var intensity3 = document.getElementById("intensity3").value;
            var intensity4 = document.getElementById("intensity4").value;

            var xhttp = new XMLHttpRequest();
            xhttp.open("GET", "/set_values?intensity1=" + intensity1 + "&intensity2=" + intensity2 + "&intensity3=" + intensity3 + "&intensity4=" + intensity4, true);
            xhttp.send();
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>ESP8266 Input Control</h1>
        <p>Enter four intensity values:</p>
        <input type="number" id="intensity1" placeholder="Value 1">
        <input type="number" id="intensity2" placeholder="Value 2">
        <input type="number" id="intensity3" placeholder="Value 3">
        <input type="number" id="intensity4" placeholder="Value 4">
        <br><br>
        <button class="button" onclick="sendValues()">Send Values</button>
    </div>
</body>
</html>
)rawliteral";

void setup() {
    Serial.begin(9600);

    // Initialize LED pins as outputs and turn them off
    pinMode(LED_PIN1, OUTPUT);
    analogWrite(LED_PIN1, 0);
    pinMode(LED_PIN2, OUTPUT);
    analogWrite(LED_PIN2, 0);
    pinMode(LED_PIN3, OUTPUT);
    analogWrite(LED_PIN3, 0);

    pinMode(LED_PIN4, OUTPUT);
    analogWrite(LED_PIN4, 0);
    pinMode(LED_PIN5, OUTPUT);
    analogWrite(LED_PIN5, 0);
    pinMode(LED_PIN6, OUTPUT);
    analogWrite(LED_PIN6, 0);

    // Connect to WiFi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    unsigned long startTime = millis();
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
        if (millis() - startTime > 15000) { // Timeout after 15 seconds
            Serial.println("\nFailed to connect to WiFi.");
            return;
        }
    }

    Serial.println("\nConnected to WiFi");
    Serial.print("ESP8266 Web Server IP Address: ");
    Serial.println(WiFi.localIP());

    // Set up server routes
    server.on("/", HTTP_GET, []() {
        server.send(200, "text/html", HTML_PAGE);
    });

    // Route to receive intensity values from the web interface
    server.on("/set_values", HTTP_GET, []() {
        if (server.hasArg("intensity1")) intensity1 = server.arg("intensity1").toInt();
        if (server.hasArg("intensity2")) intensity2 = server.arg("intensity2").toInt();
        if (server.hasArg("intensity3")) intensity3 = server.arg("intensity3").toInt();
        if (server.hasArg("intensity4")) intensity4 = server.arg("intensity4").toInt();

        Serial.println("Received Values:");
        Serial.print("Intensity 1: "); Serial.println(intensity1);
        Serial.print("Intensity 2: "); Serial.println(intensity2);
        Serial.print("Intensity 3: "); Serial.println(intensity3);
        Serial.print("Intensity 4: "); Serial.println(intensity4);

        server.send(200, "text/plain", "Values received successfully!");
    });

    server.begin();

    // Attach servos to pins
    s1.attach(0);
    s2.attach(2);
}

void loop() {
    server.handleClient();

    // Control LEDs and Servos based on intensity1
    if (intensity1 > 80) {
        digitalWrite(LED_PIN1, LOW);
        digitalWrite(LED_PIN2, LOW);
        digitalWrite(LED_PIN3, HIGH);
    } else if (intensity1 > 50) {
        digitalWrite(LED_PIN1, HIGH);
        digitalWrite(LED_PIN2, LOW);
        digitalWrite(LED_PIN3, LOW);
        s1.write(0);
        delay(150);
        s1.write(90);
        delay(150);
    } else if (intensity1 > 30) {
        digitalWrite(LED_PIN1, HIGH);
        digitalWrite(LED_PIN2, HIGH);
        digitalWrite(LED_PIN3, HIGH);
        s1.write(0);
        delay(500);
        s1.write(90);
        delay(500);
    } else {
        digitalWrite(LED_PIN1, LOW);
        digitalWrite(LED_PIN2, HIGH);
        digitalWrite(LED_PIN3, LOW);
    }

    // Control LEDs and Servos based on intensity2
    if (intensity2 > 80) {
        digitalWrite(LED_PIN4, LOW);
        digitalWrite(LED_PIN5, LOW);
        digitalWrite(LED_PIN6, HIGH);
    } else if (intensity2 > 50) {
        digitalWrite(LED_PIN4, HIGH);
        digitalWrite(LED_PIN5, LOW);
        digitalWrite(LED_PIN6, LOW);
        s2.write(0);
        delay(150);
        s2.write(90);
        delay(150);
    } else if (intensity2 > 30) {
        digitalWrite(LED_PIN4, HIGH);
        digitalWrite(LED_PIN5, HIGH);
        digitalWrite(LED_PIN6, HIGH);
        s2.write(0);
        delay(500);
        s2.write(90);
        delay(500);
    } else {
        digitalWrite(LED_PIN4, LOW);
        digitalWrite(LED_PIN5, HIGH);
        digitalWrite(LED_PIN6, LOW);
    }
}
