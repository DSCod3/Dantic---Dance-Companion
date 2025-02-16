#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <Servo.h> // servo library  
 
 Servo s1;
 Servo s2;
#define LED_PIN1 D6// red
#define LED_PIN2 D7//green
#define LED_PIN3 D8//blue

#define LED_PIN4 D0//red
#define LED_PIN5 D1//green
#define LED_PIN6 D2//blue

const char* ssid = "Jim";  
const char* password = "12345678";  
WiFiUDP udp;  
const int udpPort = 4210;  // UDP port
char packetBuffer[255];  

int intensity1 = 0;  // Variable to store first intensity value
int intensity2 = 0;  // Variable to store second intensity value



void setup() {
     Serial.begin(9600);
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("\nConnected to Wi-Fi");
     Serial.print("IP Address: ");
  Serial.println(WiFi.localIP()); // Added line to print IP address
  
    udp.begin(udpPort);
    Serial.println("UDP Server Started");
    
   
    pinMode(LED_PIN1, OUTPUT);
    analogWrite(LED_PIN1, 0); 
    pinMode(LED_PIN2, OUTPUT);
    analogWrite(LED_PIN2, 0);
    pinMode(LED_PIN3, OUTPUT);
    analogWrite(LED_PIN3, 0);// Start with LED OFF

     pinMode(LED_PIN4, OUTPUT);
    analogWrite(LED_PIN4, 0); 
    pinMode(LED_PIN5, OUTPUT);
    analogWrite(LED_PIN5, 0);
    pinMode(LED_PIN6, OUTPUT);
    analogWrite(LED_PIN6, 0);

    s1.attach(0);
     s2.attach(2);
}

void loop() {

     int packetSize = udp.parsePacket();
   
    if (packetSize) {
        int len = udp.read(packetBuffer, sizeof(packetBuffer) - 1);
        if (len > 0) {
            packetBuffer[len] = '\0';  // Null-terminate string
        }
       
        // Parse received data (format: "intensity1,intensity2")
        sscanf(packetBuffer, "%d,%d", &intensity1, &intensity2);

        // Print values for debugging
        Serial.print("Intensity 1: ");
        Serial.print(intensity1);
        Serial.print(" | Intensity 2: ");
        Serial.println(intensity2);
    }
    
    if(intensity1>80)//LED's and Servos
    {
      digitalWrite(LED_PIN1, LOW);
      digitalWrite(LED_PIN2, LOW);
      digitalWrite(LED_PIN3, HIGH);
    } else if(intensity1>50)
    {
      digitalWrite(LED_PIN1, HIGH);
      digitalWrite(LED_PIN2, LOW);
      digitalWrite(LED_PIN3, LOW);
       s1.write(0);  
      delay(150);  
      s1.write(90);
      delay(150);
      
     }else if(intensity1>30)
     {digitalWrite(LED_PIN1, HIGH);
      digitalWrite(LED_PIN2, HIGH);
      digitalWrite(LED_PIN3, HIGH);

       s1.write(0);  
      delay(500);  
      s1.write(90);
      delay(500); 
      
      }else{
        
        digitalWrite(LED_PIN1, LOW);
      digitalWrite(LED_PIN2, HIGH);
      digitalWrite(LED_PIN3, LOW);
        }

if(intensity2>80)//LED's and Servos
    {
      digitalWrite(LED_PIN4, LOW);
      digitalWrite(LED_PIN5, LOW);
      digitalWrite(LED_PIN6, HIGH);
    } else if(intensity2>50)
    {
      digitalWrite(LED_PIN4, HIGH);
      digitalWrite(LED_PIN5, LOW);
      digitalWrite(LED_PIN6, LOW);
      s2.write(0);  
      delay(150);  
      s2.write(90);
      delay(150);
      
     }else if(intensity2>30)
     {digitalWrite(LED_PIN4, HIGH);
      digitalWrite(LED_PIN5, HIGH);
      digitalWrite(LED_PIN6, HIGH);

      s2.write(0);  
      delay(500);  
      s2.write(90);
      delay(500); 
      
      }else{
        
        digitalWrite(LED_PIN4, LOW);
      digitalWrite(LED_PIN5, HIGH);
      digitalWrite(LED_PIN6, LOW);
        
        
        }
}   
