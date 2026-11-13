#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <math.h>

// ---------- Set these before flashing ----------
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
// Use your laptop's Wi-Fi IPv4 address, never 127.0.0.1 from an ESP32.
const char* API_URL = "http://192.168.1.10:8000/sensors/readings";
const char* DEVICE_KEY = "drishti-dev-key";
const char* NODE_ID = "drishti-node-01";

const int SOIL_PIN = 34;
const int RAIN_ANALOG_PIN = 35;
const int RAIN_DIGITAL_PIN = 27;
const int BATTERY_PIN = 32;       // optional voltage-divider input
const uint8_t MPU_ADDR = 0x68;
const unsigned long POST_INTERVAL_MS = 5000;

float baselineX = 0, baselineY = 0;
unsigned long lastPost = 0;

void writeMPU(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(MPU_ADDR); Wire.write(reg); Wire.write(value); Wire.endTransmission(true);
}

bool readTilt(float &tiltX, float &tiltY) {
  Wire.beginTransmission(MPU_ADDR); Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)MPU_ADDR, 6, true) != 6) return false;
  int16_t ax = (Wire.read()<<8)|Wire.read(), ay = (Wire.read()<<8)|Wire.read(), az = (Wire.read()<<8)|Wire.read();
  tiltX = atan2f((float)ay, sqrtf((float)ax*ax + (float)az*az)) * 180.0f / PI;
  tiltY = atan2f(-(float)ax, sqrtf((float)ay*ay + (float)az*az)) * 180.0f / PI;
  return true;
}

void calibrateTilt() {
  float sx=0, sy=0, x=0, y=0; int good=0;
  for (int i=0;i<100;i++) { if(readTilt(x,y)){sx+=x;sy+=y;good++;} delay(20); }
  if(good){baselineX=sx/good;baselineY=sy/good;}
  Serial.printf("CALIBRATED baseline_x=%.2f baseline_y=%.2f samples=%d\n",baselineX,baselineY,good);
}

void connectWiFi() {
  if(WiFi.status()==WL_CONNECTED) return;
  WiFi.mode(WIFI_STA); WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  Serial.print("Connecting Wi-Fi");
  for(int i=0;i<30 && WiFi.status()!=WL_CONNECTED;i++){delay(500);Serial.print(".");}
  Serial.println(WiFi.status()==WL_CONNECTED ? " connected" : " failed; retrying later");
  if(WiFi.status()==WL_CONNECTED) Serial.println("ESP32 IP: "+WiFi.localIP().toString());
}

void postReading() {
  connectWiFi(); if(WiFi.status()!=WL_CONNECTED) return;
  float x=0,y=0; if(!readTilt(x,y)){Serial.println("MPU6050 read failed");return;}
  x-=baselineX; y-=baselineY;
  int soilRaw=analogRead(SOIL_PIN), rainRaw=analogRead(RAIN_ANALOG_PIN);
  float soilPct=constrain((4095-soilRaw)*100.0f/4095.0f,0,100);
  float rainPct=constrain((4095-rainRaw)*100.0f/4095.0f,0,100);
  bool rainActive=digitalRead(RAIN_DIGITAL_PIN)==LOW;
  float battery=analogRead(BATTERY_PIN)*3.3f/4095.0f*2.0f;
  String body="{\"node_id\":\""+String(NODE_ID)+"\",\"tilt_x\":"+String(x,3)+",\"tilt_y\":"+String(y,3)+",\"soil_moisture\":"+String(soilPct,1)+",\"rain_wetness\":"+String(rainPct,1)+",\"rain_active\":"+(rainActive?"true":"false")+",\"battery\":"+String(battery,2)+"}";
  HTTPClient http; http.begin(API_URL); http.addHeader("Content-Type","application/json"); http.addHeader("X-Device-Key",DEVICE_KEY);
  int code=http.POST(body); String response=http.getString(); http.end();
  Serial.printf("POST %d | tilt=%.2f soil=%.0f%% rain=%.0f%% battery=%.2fV | %s\n",code,sqrtf(x*x+y*y),soilPct,rainPct,battery,response.c_str());
}

void setup() {
  Serial.begin(115200); pinMode(RAIN_DIGITAL_PIN,INPUT_PULLUP); analogReadResolution(12);
  Wire.begin(21,22); writeMPU(0x6B,0x00); delay(200); calibrateTilt(); connectWiFi();
  Serial.println("DRISHTI PHYSICAL SENSOR MODE — authenticated live packets enabled");
}

void loop() {
  if(millis()-lastPost>=POST_INTERVAL_MS){lastPost=millis();postReading();}
  delay(20);
}
