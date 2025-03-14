#define PWMA 5  // Right motor speed (PWM)
#define PWMB 6  // Left motor speed (PWM)
#define AIN 7   // Right motor direction
#define BIN 8   // Left motor direction
#define STBY 3  // Standby pin

void setup() {
    Serial.begin(9600);
    pinMode(PWMA, OUTPUT);
    pinMode(PWMB, OUTPUT);
    pinMode(AIN, OUTPUT);
    pinMode(BIN, OUTPUT);
    pinMode(STBY, OUTPUT);
    digitalWrite(STBY, HIGH);  // Enable motors
    Serial.println("Arduino Ready");
}

void moveForward(int speed) {
    analogWrite(PWMA, speed);
    analogWrite(PWMB, speed);
    digitalWrite(AIN, HIGH);
    digitalWrite(BIN, HIGH);
    Serial.println("Moving Forward");  // Send feedback
}

void moveBackward(int speed) {
    analogWrite(PWMA, speed);
    analogWrite(PWMB, speed);
    digitalWrite(AIN, LOW);
    digitalWrite(BIN, LOW);
    Serial.println("Moving Backward");
}

void turnLeft(int speed) {
    analogWrite(PWMA, speed / 2);
    analogWrite(PWMB, speed);
    digitalWrite(AIN, HIGH);
    digitalWrite(BIN, HIGH);
    Serial.println("Turning Left");
}

void turnRight(int speed) {
    analogWrite(PWMA, speed);
    analogWrite(PWMB, speed / 2);
    digitalWrite(AIN, HIGH);
    digitalWrite(BIN, HIGH);
    Serial.println("Turning Right");
}

void stopCar() {
    digitalWrite(PWMA, LOW);
    digitalWrite(PWMB, LOW);
    Serial.println("Car Stopped");
}

void loop() {
    if (Serial.available()>0) {
        String command = Serial.readStringUntil('\n');  // Read until newline
        command.trim();  // Remove any extra whitespace
        
        if (command.length() > 0) {
            Serial.print("Received: ");
            Serial.println(command);
        
            if (command == "w") moveForward(150);
            else if (command == "s") moveBackward(150);
            else if (command == "a") turnLeft(150);
            else if (command == "d") turnRight(150);
            else if (command == "x") stopCar();
            else Serial.println("Invalid command");
        }
    }
}
