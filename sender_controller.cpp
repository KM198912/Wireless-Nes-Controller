#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// pins you’ve chosen for the four lines
#define PIN_CLOCK 21   // green wire
#define PIN_LATCH 22   // black wire
#define PIN_DATA  23   // yellow wire

// onboard blue LED (on most devkits)
#define LED_PIN 2
// ground goes to any GND pin on the ESP32
#define BTN_A      (1 << 0)
#define BTN_B      (1 << 1)
#define BTN_SELECT (1 << 2)
#define BTN_START  (1 << 3)
#define BTN_UP     (1 << 4)
#define BTN_DOWN   (1 << 5)
#define BTN_LEFT   (1 << 6)
#define BTN_RIGHT  (1 << 7)

// BLE service/characteristic UUIDs (randomly generated)
#define SERVICE_UUID "12345678-1234-1234-1234-1234567890ab"
#define CHAR_UUID    "abcdefab-1234-5678-1234-abcdefabcdef"

// read a byte from the NES connector
uint8_t readNES() {
    uint8_t b = 0;
    digitalWrite(PIN_LATCH, HIGH);
    delayMicroseconds(12);
    digitalWrite(PIN_LATCH, LOW);
    for (int i = 0; i < 8; i++) {
        digitalWrite(PIN_CLOCK, LOW);
        delayMicroseconds(6);
        if (digitalRead(PIN_DATA) == LOW) b |= 1 << i;
        digitalWrite(PIN_CLOCK, HIGH);
        delayMicroseconds(6);
    }
    return b;
}

BLECharacteristic *pCharacteristic;
volatile bool clientConnected = false;

class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* /*pServer*/) override {
        clientConnected = true;
        Serial.println("server callback: central connected");
    }
    void onDisconnect(BLEServer* /*pServer*/) override {
        clientConnected = false;
        Serial.println("server callback: central disconnected");
    }
};

void setup() {
    pinMode(PIN_LATCH, OUTPUT);
    pinMode(PIN_CLOCK, OUTPUT);
    pinMode(PIN_DATA, INPUT_PULLUP);
    pinMode(LED_PIN, OUTPUT);

    Serial.begin(9600);

    // BLE peripheral setup
    BLEDevice::init("NES-Controller");
    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());
    BLEService *pService = pServer->createService(SERVICE_UUID);
    pCharacteristic = pService->createCharacteristic(
        CHAR_UUID,
        BLECharacteristic::PROPERTY_NOTIFY
    );
    pCharacteristic->addDescriptor(new BLE2902());
    pService->start();
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    // basic advertising; additional parameters not available in this API
    pAdvertising->start();
    // some boards prefer calling this too
    BLEDevice::startAdvertising();
    Serial.println("BLE peripheral started");
    Serial.printf("addr=%s\n", BLEDevice::getAddress().toString().c_str());
}

void loop() {
    uint8_t state = readNES();
    static uint8_t lastState = 0xFF;

    if (clientConnected && state != lastState) {
        pCharacteristic->setValue(&state, 1);
        pCharacteristic->notify();
        lastState = state;
        Serial.printf("notified 0x%02X\n", state);
    }

    // status print every few seconds
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint > 5000) {
        lastPrint = millis();
        // advertising status not exposed; only print connection flag
        Serial.printf("conn=%d\n", clientConnected);
    }

    // blink LED when waiting, solid on when a central is connected
    static unsigned long blinkLast = 0;
    if (!clientConnected) {
        if (millis() - blinkLast > 500) {
            blinkLast = millis();
            digitalWrite(LED_PIN, !digitalRead(LED_PIN));
        }
    } else {
        digitalWrite(LED_PIN, HIGH);
    }

    delay(8);  // ~120 Hz sampling rate
}