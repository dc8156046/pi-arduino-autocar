#define TRIG 9  // ultrasonic sensor TRIG pin
#define ECHO 10 // ultrasonic sensor ECHO pin
#define PWMA 5  // right motor speed
#define PWMB 6  // left motor speed
#define AIN 7   // right motor direction
#define BIN 8   // left motor direction
#define STBY 3  // standby pin

void setup() {
    Serial.begin(9600);
    pinMode(TRIG, OUTPUT);
    pinMode(ECHO, INPUT);
    pinMode(PWMA, OUTPUT);
    pinMode(PWMB, OUTPUT);
    pinMode(AIN, OUTPUT);
    pinMode(BIN, OUTPUT);
    pinMode(STBY, OUTPUT);
    digitalWrite(STBY, HIGH);
    Serial.println("Arduino Ready");
}

long getDistance() {
    digitalWrite(TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG, LOW);
    long duration = pulseIn(ECHO, HIGH);
    return duration * 0.034 / 2; // convert time to distance
}

void moveForward(int speed) {
    if (getDistance() < 15) {  // stop if obstacle is detected within 15cm
        stopCar();
        Serial.println("Obstacle detected! Stopping.");
        return;
    }
    analogWrite(PWMA, speed);
    analogWrite(PWMB, speed);
    digitalWrite(AIN, HIGH);
    digitalWrite(BIN, HIGH);
    Serial.println("Moving Forward");
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
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n'); // read command until newline from serial port
        command.trim();
        
        if (command.length() > 0) {
            Serial.print("Received: ");
            Serial.println(command); // print received command to serial monitor for debugging
            
            if (command == "w") moveForward(150);
            else if (command == "s") moveBackward(150);
            else if (command == "a") turnLeft(150);
            else if (command == "d") turnRight(150);
            else if (command == "x") stopCar();
            else if (command == "distance") {
                long distance = getDistance();
                Serial.print("Distance: ");
                Serial.println(distance);
            }
            else Serial.println("Invalid command");
        }
    }
}
