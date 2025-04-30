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
bool printData = true;  // controls printing data to serial monitor
bool saveData = true;   // controls saving data to microSD
String inputBuffer = ""; // Buffer to store incoming characters

void setup() {                                                      
    Serial.begin(9600); // ensure baud rate is synced in serial monitor
    pinMode(sensorPin, INPUT); //

    Serial.println("Initializing SD card...");
    delay(500);  // Allow SD card to power up

    SPI.begin(CLK, DO, DI, CS);  // Assign SPI pins in this order!!!

    if (!SD.begin(CS)) {
        Serial.println("\n Card Mount Failed!"); // This will not recognize microSD breakout board without microSD inserted
        return;
    }

    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE) {
        Serial.println("\n No SD card detected - Insert a card."); // This was a useless addition because the breakout board can't be initialized without the microSD card
        return;
    }

    Serial.println("SD Card Initialized!");
    sdInitialized = true; // Include this to cue in the function for other parts of the code

    Serial.println("\nType 's' to start recording for 2 minutes.");
}

void loop() {
    if (!collecting && Serial.available()) {
        char input = Serial.read();
        if (input == 's' || input == 'S') {
            Serial.println("\nEnter filename to save data (e.g., data.csv):");
            while (!Serial.available());  // Will not continue without pressing s or a file name

            String filename = Serial.readString(); // create file name command
            filename.trim();
            if (!filename.startsWith("/")) {
                filename = "/" + filename;
            }
            if (!filename.endsWith(".csv")) {
                filename += ".csv";  // This is to ensure file has a csv extension so that user doesn't have to worry
               
            }

            startDataCollection(filename.c_str()); 
        }
    }

    // Continuously check for the "stop" command while collecting data ~ THIS DOESN"T WORK
    if (collecting && Serial.available()) {
        char input = Serial.read();  // Reads each byte
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
        file = SD.open(filename, FILE_WRITE); // I stole this from the example
        if (!file) {
            Serial.println("Failed to open file!");
            return;
        }

        file.println("Time (ms), Conductance (µS)"); // This is the CSV Header so it stores as two separate columns
    }

    unsigned long startTime = millis();  // assigns current sample time to each ms following start time
    unsigned long lastSampleTime = 0; // starts sample time at 0
    collecting = true;

    while (collecting && millis() - startTime < duration) { // This ensures collection is only within the duration period, in this case 120000ms
        unsigned long currentTime = millis();
        if (currentTime - lastSampleTime >= samplingInterval) {
            lastSampleTime = currentTime; // this continues the collection loop

            float skinConductance = measureSkinConductance(); // This assigns values from equation to a variable
            String dataLine = String(currentTime - startTime) + "," + String(skinConductance, 2); // this creates how the data will be stored on microSD
            
            // Save data to SD if saveData flag is true
            if (saveData) {
                file.println(dataLine); // prints both time and skin conductance
            
            if (printData) {
                Serial.println(skinConductance, 4); // this prints only skin conductance to 
            }
        }
    }

    if (saveData) {
        file.flush(); // forces data out of memory and onto SD card
        file.close(); // closes file after storing all of the data
        Serial.print("\nData saved to: "); 
        Serial.println(filename);
    }

    // Ask if user wants to start again
    Serial.println("\nWould you like to start a new session? (y/n)"); // Once session is over
    while (!Serial.available());

    char restart = Serial.read();
    if (restart == 'y' || restart == 'Y') {
        Serial.println("\nType 's' to start recording for 2 minutes."); // this starts the loop over again
    } else {
        Serial.println("\nStopping program.");
        while (true);  // Stop execution
    }

    collecting = false; // reset 
}

float measureSkinConductance() { // equations for converting analog values from ESP32 to digital output values
    int analog = analogRead(sensorPin);
    float V_in = 3.3;
    float V_out = (((float)analog / 4096) * V_in + 0.1258);
    int R_1 = 1000000;
    int R_2 = 1000000;
    int R_4 = 1000000;
    float R_skin = (1000000 * (float)V_out)/(V_in - V_out);
    float conductance = 1 / R_skin;
    return conductance * 1e6 + 0.04; // sends skin conductance values to collection loop as "measureSkinConductance"
}

