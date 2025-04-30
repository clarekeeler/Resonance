#include "FS.h"
#include "SD.h"
#include "SPI.h"

// Define SPI pins
#define CLK 18  // SCK (Serial Clock)
#define DI 23   // MOSI (Master Out Slave In)
#define DO 19   // MISO (Master In Slave Out)
#define CS 21   // CS (Chip Select)

const int sensorPin = 4;
const int samplingInterval = 200;  // change this to change sample rate (in ms)
const int duration = 120000;       // change this to change interval (in ms)
bool sdInitialized = false;
bool collecting = false;
bool printData = true;  // Flag to control printing data
bool saveData = true;   // Flag to control saving data to microSD
String inputBuffer = ""; // Buffer to store incoming characters

void setup() {                                                      
    Serial.begin(9600);
    pinMode(sensorPin, INPUT);

    Serial.println("Initializing SD card...");
    delay(500);  // Allow SD card to power up

    SPI.begin(CLK, DO, DI, CS);  // Manually set SPI pins

    if (!SD.begin(CS)) {
        Serial.println("\n Card Mount Failed!");
        return;
    }

    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE) {
        Serial.println("\n No SD card detected - Insert a card.");
        return;
    }

    Serial.println("SD Card Initialized!");
    sdInitialized = true;

    Serial.println("\nType 's' to start recording for 2 minutes.");
}

void loop() {
    if (!collecting && Serial.available()) {
        char input = Serial.read();
        if (input == 's' || input == 'S') {
            Serial.println("\nEnter filename to save data (e.g., data.csv):");
            while (!Serial.available());  // Wait for user input

            String filename = Serial.readString();
            filename.trim();
            if (!filename.startsWith("/")) {
                filename = "/" + filename;
            }
            if (!filename.endsWith(".csv")) {
                filename += ".csv";  // Ensure file has .csv extension
               
            }

            startDataCollection(filename.c_str());
        }
    }

    // Continuously check for the "stop" command while collecting data
    if (collecting && Serial.available()) {
        char input = Serial.read();  // Read incoming byte
        inputBuffer += input;        // Append byte to buffer
        
        // Check if the "stop" command is in the input buffer
        if (inputBuffer.endsWith("stop")) {
            Serial.println("\nData collection stopped.");
            collecting = false;   // Stop data collection
            printData = false;    // Stop printing data to the Serial Monitor
            saveData = false;     // Stop saving data to the microSD
        }
    }
}

void startDataCollection(const char* filename) {
    Serial.println("Recording started for 2 minutes...");

    File file;
    if (saveData) {
        file = SD.open(filename, FILE_WRITE);
        if (!file) {
            Serial.println("Failed to open file!");
            return;
        }

        // Write CSV header
        file.println("Time (ms), Conductance (µS)");
    }

    unsigned long startTime = millis();
    unsigned long lastSampleTime = 0;
    collecting = true;

    while (collecting && millis() - startTime < duration) {
        unsigned long currentTime = millis();
        if (currentTime - lastSampleTime >= samplingInterval) {
            lastSampleTime = currentTime;

            float skinConductance = measureSkinConductance();
            String dataLine = String(currentTime - startTime) + "," + String(skinConductance, 2);
            
            // Save data to SD if saveData flag is true
            if (saveData) {
                file.println(dataLine);
            }

            // Print data only if the printData flag is true
            if (printData) {
                Serial.println(skinConductance, 4);
            }
        }
    }

    if (saveData) {
        file.flush();
        file.close();
        Serial.print("\nData saved to: ");
        Serial.println(filename);
    }

    // Ask if user wants to start again
    Serial.println("\nWould you like to start a new session? (y/n)");
    while (!Serial.available());

    char restart = Serial.read();
    if (restart == 'y' || restart == 'Y') {
        Serial.println("\nType 's' to start recording for 2 minutes.");
    } else {
        Serial.println("\nStopping program.");
        while (true);  // Stop execution
    }

    collecting = false;
}

float measureSkinConductance() {
    int analog = analogRead(sensorPin);
    float V_in = 3.3;
    float V_out = (((float)analog / 4096) * V_in + 0.1258);
    int R_1 = 1000000;
    int R_2 = 1000000;
    int R_4 = 1000000;
    float R_skin = (1000000 * (float)V_out)/(V_in - V_out);
    float conductance = 1 / R_skin;
    return conductance * 1e6 + 0.04;
}

