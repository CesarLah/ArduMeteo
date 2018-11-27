  /* The aim for this sketch is to acquire values from different sensors (thermometer(LM335), pluviometer (tipping bucket),
  anemometer (NRG 40C), wind vane (NRG 40C) and a Light Diode Resistance (GP5516L)) and send the values obtained to a server. 
  Each 3 seconds a new sample for every sensor is acquired and stored in a variable. Once 200 samples are registered (about ten minutes), a small statistics 
  for each sensor is done, given the corresponding measures: values average, maximun, minimun and the standard deviation for each magnitude. When six 
  measures are got,the SM5100B GPRS module is ordered to send data which was previously stored at the EEPROM memory to the indicated IP. When data are sent,
  the connection with the socket is closed and the loop continues (acquiring data).
  For data processing, see the script ArduINTERMET.py.
  The functions related with the GPRS module are based in the sketch from the website IMA/Tracking the island  */

//LYBRARIES INCLUDED
#include "Time.h"    //To deal with time
#include <EEPROM.h>  //To store the data permanently until is sent
#include <PString.h>  //To be able to link different character strings to send data.
#include <SoftwareSerial.h>  //To create a new Serial port for communication with SM5100B

//CONSTANTS --------------------------------
#define SAMPLE_DELAY 3000  //time between samples
#define SAMPLES 200   //number of samples
#define MEASURES 6     //number of measures
#define POSITIONS 120  //number of EEPROM positions occupied every measure to store data collected 
#define PLUVIO_SUR 78.427  //for a pluviometer surface with a mouth diameter of 0.158. pi*r^2=0.078m^2
//#define IP_INTERMET 7  //Server's IP where data is sent
//#define PORT 769       //Server's port where data is sent

//I/O PINS ----------------------------------
#define PLUVIO_PIN 20  //For interrupt signal number 5 (attachInterrupt()) 
#define ANEMO_PIN 21   //Interrupt number 2. Digital pin. 
#define VANE_PIN 15    //Analog pin
#define TEMP_PIN 10    //  "     "
#define LDR_PIN 13     //  "     "
#define POWER_PIN 18  //Digital pin
#define GPRS_TX 10    //  "      "
#define GPRS_RX 11    //  "      "


//SENSORS VARIABLES--------------------------
float tavg, tmax, tmin, tstd;    //Temperature

volatile long int num_anemo = 0;            //Anemometer interrupts counter
float vel_avg, vel_max, vel_min, vel_std; //    "

float uavg, vavg, umax, umin, ustd, vmax, vmin, vstd, direction_grades, modulus;  //Vane

volatile long int num_pluvio = 0;     //Pluviometer 
float ravg, rmax, rmin, rstd, rain_ttal_m2 = 0;        //rain_ttal_m2--> rain fallen since the Arduino was powered

float lavg, lmax, lmin, lstd;  //LDR (light diode resistance)

int min10_year, min10_month, min10_day, min10_hour, min10_minute, min10_sec; //Time every 10 minutes
                                               
int ee_count; //EEPROM cells position counter (for each hour)

//GPRS VARIABLES -------------------------
const int BUFFSIZE = 210;  
char at_buffer[BUFFSIZE];  //Buffer to communicate with the GPRS shield
char incoming_char = 0;
char buffer[BUFFSIZE];
//char buffidx;
    
const int ERROR_SIM_UNAVAIL  = 2;   //Error codes 
const int ERROR_GPRS_FAIL    = 3; 
const int ERROR_NETWORK_FAIL = 4;
const int ERROR_HOST         = 5;
const int ERROR_GPRS_UNKNOWN = 6;
const int ERROR_GSM_FAIL     = 7;
const boolean DEBUG          = true;

boolean GPRS_registered = false;  // Registers
boolean GPRS_AT_ready   = false;
boolean continueLoop    = true;
boolean firstTimeInLoop = false;

const int SEND_DELAY = 2000; // Time to wait before sending next values

SoftwareSerial cell(GPRS_TX, GPRS_RX);      //Declare a new Serial port
PString myStr(buffer, sizeof(buffer));      //Define a string object for the communication with the SM5100 module

int hour_start    = 01;   //To set date and time in the Arduino start.
int minute_start  = 18;  
int seconds_start = 00;
int day_start     = 10;
int month_start   = 5;
int year_start    = 2016;

void setup() {
  Serial.begin(9600);  // Define the baud rate for the serial communication between Arduino-Computer
  cell.begin(9600);    // Define the baud rate for the serial communication between Arduino-SM5100
  setTime(hour_start, minute_start, seconds_start, day_start, month_start, year_start);      
  
  pinMode(POWER_PIN, OUTPUT);
  digitalWrite(POWER_PIN, LOW);
  pinMode(PLUVIO_PIN, INPUT);
  digitalWrite(PLUVIO_PIN, HIGH);  //20kohm pull-up resistance activation
  pinMode(ANEMO_PIN, INPUT);
  digitalWrite(ANEMO_PIN, HIGH);  
  
  Serial.println(F("Establishing Connection")); 
  establishNetwork();                           //Connect with the GPRS server
  Serial.println(F("Connection Established"));  //The 'F' before the text means the text is read from the flash memory.
  sendInitial();                                //Connect with the indicated IP
  Serial.println("Connected with Server");

}

void loop() {
  ee_count = 0;  
  for (byte ee_count = 0; ee_count <= 4; ee_count++){  //120positions*6measures_num*5eee_loops=3600. Total EEPROM capacity 4096 bytes
    for (byte z = 0; z <= MEASURES - 1; z++){
      Serial.print(F("\nMEASURE NUMBER: "));  
      Serial.println(z);
      samplesRegister();
      timer();              //Set the time when the measure is finished
      storeEEPROM();         //Save the measure in the permanent memory 
      ee_count+=POSITIONS;    //Next position to begin to store in EEPROM. 
    }
    openTCP();      //Open data connection with server (via TCP)
    delay(500);     
    extractEEPROM(ee_count); //Get the 6 measures made in last hour
    delay(700);       //Give time until all the chains are sent
    quitTransfer();  //Say goodbye to Server
    closeTCP();      //Close data connection
  }
}

void pluvio_counter(){  //Count the number of interrupts signals for the pluviometer
num_pluvio++;
}

void anemo_counter(){  //Count the number of interrupts signals for the anemometer
num_anemo++;
}

void samplesRegister(){  //Register the signals for each sensor

  int anemo[SAMPLES] = {};  //Registers
  int rain[SAMPLES] = {};  
  int temp[SAMPLES] = {}; 
  int ldr[SAMPLES] = {};
  int vane[SAMPLES] = {};
  
  for (int i = 0; i <= SAMPLES - 1;i++){
    Serial.print(F("\nSAMPLE NUMBER: "));
    Serial.println(i);
    
    attachInterrupt(0, pluvio_counter, RISING);  //Interrupt number 5 (pin 20)
    attachInterrupt(1, anemo_counter, RISING);   //    "       "    2 (pin 21)
    num_anemo = 0;  
    num_pluvio = 0;
    delay(SAMPLE_DELAY);
    
    detachInterrupt(0);  
    rain[i] = num_pluvio;      
    Serial.print(F("Rain accumulated? (ml): "));  
    Serial.println(num_pluvio * 5);              //Tipping bucket with 5ml capacity
    
    detachInterrupt(1);
    anemo[i] = num_anemo;
    Serial.print(F("Speed (km/h): "));    
    if (num_anemo == 0) {Serial.println(F("0"));}
    else {Serial.println(((float(anemo[i]) * 765) / (2 * SAMPLE_DELAY)) + 0.35);}  //*3.6 to convert m/s in km/h.
    
    digitalWrite(POWER_PIN, HIGH);     //Current source for the analog sensors   
    
    temp[i]= analogRead(TEMP_PIN);
    Serial.print(F("Temperature: "));
    Serial.print((((float(temp[i]) / 1024.0) * 5000) / 10) - 273.15);  //Conversion factor between Volts and Celsius
    Serial.println(F(" degrees Celsius"));
    
    vane[i]= analogRead(VANE_PIN);
    Serial.print(F("Wind Direction (grades): "));    
    Serial.println((0.35156) * float(vane[i]));      //360º/1024= 0.3515625
    
    ldr[i]=analogRead(LDR_PIN);
    digitalWrite(POWER_PIN, LOW);
    Serial.print("Light level (range 0-1024): ");
    Serial.println(ldr[i]);
    }
 calculateTemp(temp);        //Calculate the average, maximun, minimum and standard deviation for the 200 samples collected
 calculateAnemo(anemo);
 calculateVane(vane,anemo);
 calculateRain(rain);
 calculateLum(ldr);
 
 Serial.println(F("\n********* RESULTS IN THIS 10 MINUTES *********"));
 showResults();
}

void calculateAnemo(int anemo[]){      
  double r = 0;
  long int  vel_ttal = 0;
  float  anemo_avg, anemo_std; 
  int anemo_max = 0, anemo_min = 1000;   //1000, maximun interrupts detected in every sample 
  for(int i = 0;i <= SAMPLES - 1; i++){
    vel_ttal+= anemo[i]; 
  }
  anemo_avg = float(vel_ttal) / (SAMPLES+1);
  for(int j = 0; j <= SAMPLES - 1; j++){
    double s = pow((float(anemo[j]) - anemo_avg), 2);
    r += s;
    if (anemo[j] >= anemo_max){anemo_max = anemo[j];}  
    if (anemo[j] <= anemo_min){anemo_min = anemo[j];}
    }
  anemo_std = sqrt(r / (SAMPLES + 1));
  if (anemo_max == 0){vel_max = 0;}
  else{vel_max = (float(anemo_max) * 765 / (2 * SAMPLE_DELAY)) + 0.35;}  //Formula given in NRG 40C datasheet
  if (anemo_min == 0){vel_min = 0;}
  else{vel_min = (float(anemo_min) * 765 / (2 * SAMPLE_DELAY)) + 0.35;}
  if (anemo_avg == 0){vel_avg = 0;}
  else{vel_avg = (anemo_avg * 765 / (2 * SAMPLE_DELAY)) + 0.35;} 
  if (anemo_std == 0){vel_std = 0;}
  else{vel_std = (anemo_std * 765 / (2 * SAMPLE_DELAY)) + 0.35;} 
}

void calculateTemp(int temp[]){
  double r = 0;
  long int t_ttal = 0;
  float temp_avg, temp_std;  //Maximun and minimun range for LM335
  int temp_max = -40, temp_min = 60;
  for(int i = 0; i <= SAMPLES-1; i++){
    t_ttal += temp[i]; 
  }
  temp_avg = float(t_ttal) / (SAMPLES + 1);
  for(int j= 0; j<= SAMPLES - 1; j++){
    double s = pow((float(temp[j]) - temp_avg), 2);
    r += s;
    if (temp[j] < temp_min){temp_min = temp[j];}  
    if (temp[j] > temp_max){temp_max = temp[j];}
    }
  temp_std = sqrt(r / (SAMPLES + 1));
  tavg = (((temp_avg / 1024) * 5000) / 10) - 273.15;    //Convert volts in celsius
  tmax = (((float(temp_max) / 1024) * 5000) / 10) - 273.15;
  tmin = (((float(temp_min) / 1024) * 5000) / 10) - 273.15;
  tstd = (((temp_std / 1024) * 5000) / 10) - 273.15;
}

void calculateRain(int rain[]){
  double r = 0;
  long int rttal = 0;
  float rain_avg, rain_std; //
  int rain_max = 0, rain_min = 500;
  for(int i= 0; i <= SAMPLES - 1; i++){
    rttal += (rain[i]);                    
  }
  rain_avg =  float(rttal) / (SAMPLES + 1);            
  for(int j = 0; j <= SAMPLES - 1; j++){
    double s = pow((float(rain[j]) - ravg), 2);
    r += s;
    if (rain[j] >= rain_max){rain_max = rain[j];}  //Pluvio
    if (rain[j] <= rain_min){rain_min = rain[j];}
    }
  rain_std = sqrt(r / (SAMPLES + 1));
  ravg = (rain_avg * 5) / PLUVIO_SUR;        // In mm(l/m2). Tipping buck capacity: 5ml
  rmax = (float(rain_max) * 5) / PLUVIO_SUR;
  rmin = (float(rain_min) * 5) / PLUVIO_SUR;
  rstd = (rain_std * 5) / PLUVIO_SUR;
  
}

void calculateLum(int ldr[]){
  double r = 0;
  float lttal;
  for(int i = 0; i <= SAMPLES - 1; i++){
    lttal += ldr[i]; 
  }
  lavg = lttal / (SAMPLES + 1);
  for(int j = 0; j <= SAMPLES - 1; j++){
    double s = pow((ldr[j] - lavg), 2);
    r += s;
    if (ldr[j] >= lmax){lmax = ldr[j];}  
    if (ldr[j] <= lmin){lmin = ldr[j];}
    }
  lstd = sqrt(r / (SAMPLES + 1));        
}

void calculateVane(int vane[], int anemo[]){
  float comp_u[SAMPLES] = {};    
  float comp_v[SAMPLES] = {};
  float uttal = 0, vttal = 0, umax = -360, umin = 360, vmax = -360, vmin = 360;    //Max. value for a 120 km/h wind speed (120*3.14=377)
  for (int i=0;i<=SAMPLES-1;i++){
    if (anemo [i]==0){
    comp_u[i]=0;
    comp_v[i]=0;
    }
    else{
    comp_u[i]=((anemo[i]*765/(2*SAMPLE_DELAY))+0.35)*(cos((0.00613592)*vane[i]));    //2*pi/1024));   
    comp_v[i]=((anemo[i]*765/(2*SAMPLE_DELAY))+0.35)*(sin((0.00613592)*vane[i]));}    //2*pi/1024));
    
    uttal += comp_u[i];
    vttal += comp_v[i];
    }
  uavg = uttal / (SAMPLES + 1);
  vavg = vttal / (SAMPLES + 1);
  float direct_vector_ttal = atan(vttal / uttal);
  double ru = 0, su = 0, rv = 0, sv = 0;
  for (int j = 0; j <= SAMPLES - 1; j++){      
    su = pow((comp_u[j] - uavg), 2);
    sv = pow((comp_v[j] - vavg), 2);
    ru += su;
    rv += sv;
    if (comp_u[j] >= umax){umax = comp_u[j];}  //Veleta
    if (comp_u[j] <= umin){umin = comp_u[j];}
    if (comp_v[j] >= vmax){vmax = comp_v[j];}
    if (comp_v[j] <= vmin){vmin = comp_v[j];}
   }   
  ustd = sqrt(ru / (SAMPLES + 1));  
  vstd = sqrt(rv / (SAMPLES + 1));
  
  if ((vttal && uttal) == 0){direct_vector_ttal = 0;}
  modulus = sqrt((pow(uttal / (SAMPLES + 1), 2)) + pow(vttal / (SAMPLES + 1), 2));
  direction_grades = (direct_vector_ttal * 360) / (2 * 3.1415926);
  if (vttal <= 0 && uttal < 0){
     direction_grades += 180;
   }
  else if (vttal < 0 && uttal >= 0) {
     direction_grades += 360;
   }
  else if (vttal > 0 && uttal < 0) {
      direction_grades += 180;
  } 
}

void timer(){  //Establish date and time when is invoked
  time_t Time1;
  Time1 = now();
  min10_year = year(Time1);        
  min10_month = month(Time1);
  min10_day = day(Time1);
  min10_hour = hour(Time1);
  min10_minute = minute(Time1);
  min10_sec = second(Time1);
}

void storeEEPROM(){    //Put in permanent memory the data acquired hourly
  EEPROM.put(ee_count, min10_hour);
  EEPROM.put(ee_count + 2, min10_minute);
  EEPROM.put(ee_count + 4, min10_sec);
  EEPROM.put(ee_count + 6, min10_day);
  EEPROM.put(ee_count + 8, min10_month);
  EEPROM.put(ee_count + 10 , min10_year);
  EEPROM.put(ee_count + 12, tavg);
  EEPROM.put(ee_count + 16, tmax);
  EEPROM.put(ee_count + 20, tmin);
  EEPROM.put(ee_count + 24, tstd);
  EEPROM.put(ee_count + 28, vel_avg);
  EEPROM.put(ee_count + 32, vel_max);
  EEPROM.put(ee_count + 36, vel_min);
  EEPROM.put(ee_count + 40, vel_std);
  EEPROM.put(ee_count + 44, direction_grades);
  EEPROM.put(ee_count + 48, modulus);
  EEPROM.put(ee_count + 52, uavg);
  EEPROM.put(ee_count + 56, umax);
  EEPROM.put(ee_count + 60, umin);
  EEPROM.put(ee_count + 64, ustd);
  EEPROM.put(ee_count + 68, vavg);
  EEPROM.put(ee_count + 72, vmax);
  EEPROM.put(ee_count + 76, vmin);
  EEPROM.put(ee_count + 80, vstd);
  EEPROM.put(ee_count + 84, ravg);
  EEPROM.put(ee_count + 88, rmax);
  EEPROM.put(ee_count + 92, rmin);
  EEPROM.put(ee_count + 96, rstd);
  EEPROM.put(ee_count + 100, rain_ttal_m2);
  EEPROM.put(ee_count + 104, lavg);
  EEPROM.put(ee_count + 108, lmax);
  EEPROM.put(ee_count + 112, lmin);
  EEPROM.put(ee_count + 116, lstd);
  Serial.println(F("\nSTORED IN MEMORY"));
} 

void extractEEPROM(int num_loops){    //Extract the 6 measures done before and send each one 
  Serial.print(F("-------------------"));
  for (int j = num_loops * POSITIONS * MEASURES; j < (num_loops + 1) * MEASURES * POSITIONS; j += POSITIONS) { 
    min10_hour   = EEPROM.get(j, min10_hour);
    min10_minute = EEPROM.get(j + 2, min10_minute);
    min10_sec    = EEPROM.get(j + 4, min10_sec);
    min10_day    = EEPROM.get(j + 6, min10_day);
    min10_month  = EEPROM.get(j + 8, min10_month);
    min10_year   = EEPROM.get(j + 10, min10_year);
    tavg = EEPROM.get(j + 12, tavg);      
    tmax = EEPROM.get(j + 16, tmax);
    tmin = EEPROM.get(j + 20, tmin);
    tstd = EEPROM.get(j + 24, tstd);
    vel_avg = EEPROM.get(j + 28, vel_avg);
    vel_max = EEPROM.get(j + 32, vel_max);
    vel_min = EEPROM.get(j + 36, vel_min);
    vel_std = EEPROM.get(j + 40, vel_std);
    direction_grades = EEPROM.get(j + 44, direction_grades);
    modulus = EEPROM.get(j + 48, modulus);
    uavg = EEPROM.get(j + 52, uavg);
    umax = EEPROM.get(j + 56, umax);
    umin = EEPROM.get(j + 60, umin);
    ustd = EEPROM.get(j + 64, ustd);
    vavg = EEPROM.get(j + 68, vavg);
    vmax = EEPROM.get(j + 72, vmax);
    vmin = EEPROM.get(j + 76, vmin);
    vstd = EEPROM.get(j + 80, vstd);
    ravg = EEPROM.get(j + 84, ravg);
    rmax = EEPROM.get(j + 88, rmax);
    rmin = EEPROM.get(j + 92, rmin);
    rstd = EEPROM.get(j + 96, rstd);
    rain_ttal_m2 = EEPROM.get(j + 100, rain_ttal_m2);    
    lavg = EEPROM.get(j + 104, lavg);
    lmax = EEPROM.get(j + 108, lmax);
    lmin = EEPROM.get(j + 112, lmin);
    lstd = EEPROM.get(j + 116, lstd);
    Serial.println(F("\nDATA TO SEND: "));
    Serial.print(F("CHAIN NUMBER: "));
    Serial.print(j);
    showResults();
    delay(SEND_DELAY);    
    sendData();  
    }
}

//store the serial string in a buffer until we receive a newline
static void readATString(boolean watchTimeout = false) {  
  char c;
  char buffidx = 0;
  int time = millis();
    
  while (1) {
    int newTime = millis();

    if (watchTimeout) {
      // Time out if we never receive a response    
      if (newTime - time > 30000) error(ERROR_GSM_FAIL);
    }
    
    if (cell.available() > 0) {
      c = cell.read();            
      if (c == -1) {
        at_buffer[buffidx] = '\0';
        return;
      }      
      if (c == '\n') {
        continue;
      }     
      if ((buffidx == BUFFSIZE - 1) || c == '\r') {
        at_buffer[buffidx] = '\0';
        return;
      }
      
      at_buffer[buffidx++] = c;
    } 
  }
}

static void establishNetwork() {    //Establish the connection to the GPRS network
  while (GPRS_registered == false || GPRS_AT_ready == false) {
    readATString(true);
    ProcessATString();
  }
}

static void sendATCommand(const char* ATCom) {    
  cell.println(ATCom);
  Serial.print(F("COMMAND: "));
  Serial.println(ATCom);
  
  while (continueLoop) {
    readATString();
    ProcessATString();
    Serial.print(F("RESPONSE: "));
    Serial.println(at_buffer);
  }
  
  continueLoop = true;
  delay(500);
}

static void sendInitial() {      //Function to connect with the Server

  Serial.println(F("Setting up PDP Context"));
  sendATCommand("AT+CGDCONT=1,\"IP\",\"movistar.es\"");  // PDP context identifier  
  Serial.println(F("Configure APN"));
  sendATCommand("AT+CGPCO=0,\"MOVISTAR\",\"MOVISTAR\", 1");  // 0 = >ASCII characters, user, password, 1 => PDP identity
  
  Serial.println(F("Activate PDP Context already specified (IP)"));  // PDP context activated en PDP ID = 1
  sendATCommand("AT+CGACT=1,1");         
  
 
  Serial.println(F("Configuring TCP connection to server"));
  sendATCommand("AT+SDATACONF=1,\"TCP\",\"95.22.21.151\",769");    // HERE IS THE IP TO CONNECT TO AND THE PORT.
    
  Serial.println(F("Starting TCP Connection"));
  sendATCommand("AT+SDATASTART=1,1");      // GPRS service activated
}  

static void openTCP(){    // GPRS service activated
  delay(1000); 
  Serial.println(F("Opening data connection with server"));
  sendATCommand("AT+SDATASTART=1,1"); 
}

static void closeTCP(){  //Deactivate GPRS service
  delay(1000);
  Serial.println(F("Closing TCP connection"));
  sendATCommand("AT+SDATASTART=1,0");   
}

static void sendData(){      //Create a big character chain and send it 

  Serial.println(F("Sending data: "));
  myStr.begin();                        //Clears the string "myStr"
  myStr.print("AT+SSTRSEND=1,\"");
  myStr.print("i999000");
  myStr.print(";");
  myStr.print(min10_hour, DEC);
  myStr.print(";");
  myStr.print(min10_minute, DEC);
  myStr.print(";");
  myStr.print(min10_sec, DEC);
  myStr.print(";");  
  myStr.print(min10_day, DEC);
  myStr.print(";");
  myStr.print(min10_month, DEC);
  myStr.print(";");
  myStr.print(min10_year, DEC);
  myStr.print(";");
  myStr.print(tavg, 2);
  myStr.print(";");
  myStr.print(tmax, 2);
  myStr.print(";");
  myStr.print(tmin, 2);
  myStr.print(";");
  myStr.print(tstd, 3);
  myStr.print(";");  
  myStr.print(vel_avg, 2);
  myStr.print(";");
  myStr.print(vel_max, 2);
  myStr.print(";");
  myStr.print(vel_min, 2);
  myStr.print(";");
  myStr.print(vel_std, 2);
  myStr.print(";");
  myStr.print(direction_grades, 2);
  myStr.print(";");
  myStr.print(modulus);
  myStr.print(";");
  myStr.print(uavg, 1);  //With only 1 decimal  
  myStr.print(";");
  myStr.print(umax, 1);
  myStr.print(";");
  myStr.print(umin, 1);
  myStr.print(";");
  myStr.print(ustd, 1);
  myStr.print(";");
  myStr.print(vavg, 1);
  myStr.print(";");
  myStr.print(vmax, 1);
  myStr.print(";");
  myStr.print(vmin, 1);
  myStr.print(";");
  myStr.print(vstd, 1);
  myStr.print(";");
  myStr.print(ravg, 2);
  myStr.print(";");
  myStr.print(rmax, 2);
  myStr.print(";");
  myStr.print(rmin, 2);
  myStr.print(";");
  myStr.print(rstd, 2);
  myStr.print(";");
  myStr.print(rain_ttal_m2);
  myStr.print(";");
  myStr.print(lavg, 2);
  myStr.print(";");
  myStr.print(lmax, 2);
  myStr.print(";");
  myStr.print(lmin, 2);
  myStr.print(";");
  myStr.print(lstd, 2);
  myStr.print("\"");
  sendATCommand(myStr);
  delay(100);
  myStr.begin();
}

static void quitTransfer(){    // Send an indication that the sending is finished
  myStr.begin();
  delay(200);
  myStr.print("AT+SSTRSEND=1,\"quit\"");
  sendATCommand(myStr);
  Serial.print("Data Sent. ");
  myStr.begin();
}

static void ProcessATString() {    // Handle response codes. Process what GPRS module say to Arduino 
  
  if (DEBUG) {
    Serial.println(at_buffer);
  }
  
  if (strstr(at_buffer, "+SIND: 1" ) != 0) {
    firstTimeInLoop = true;
    GPRS_registered = false;
    GPRS_AT_ready = false;
  }
  
  if (strstr(at_buffer, "+SIND: 10,\"SM\",0,\"FD\",0,\"LD\",0,\"MC\",0,\"RC\",0,\"ME\",0") != 0 
    || strstr(at_buffer, "+SIND: 0") != 0) {
    error(ERROR_SIM_UNAVAIL);
  }
  
  if (strstr(at_buffer, "+SIND: 10,\"SM\",1,\"FD\",1,\"LD\",1,\"MC\",1,\"RC\",1,\"ME\",1") != 0) {
    Serial.println(F("SIM card Detected"));
  }
  
  if (strstr(at_buffer, "+SIND: 7") != 0) {
    error(ERROR_NETWORK_FAIL);  
  }
  
  if (strstr(at_buffer, "+SIND: 8") != 0) {
    GPRS_registered = false;
    error(ERROR_GPRS_FAIL);
  }
  
  if (strstr(at_buffer, "+SIND: 11") != 0) {
    GPRS_registered = true;
    Serial.println(F("GPRS Registered"));
  }
  
  if (strstr(at_buffer, "+SIND: 4") != 0) {
     GPRS_AT_ready = true;
     Serial.println(F("GPRS AT Ready"));

  }
  
  if (strstr(at_buffer, "+SOCKSTATUS:  1,0") != 0) {
     error(ERROR_HOST);
  }
  
  if (strstr(at_buffer, "+CME ERROR: 29") != 0) {
    continueLoop = false;
    return;
  }
  
  if (strstr(at_buffer, "+CME ERROR") != 0) {
    error(ERROR_GPRS_UNKNOWN);
  }
  
  if (strstr(at_buffer, "OK") != 0 || strstr(at_buffer, "NO CARRIER") != 0) {
    continueLoop = false;

  }
  
  if (strstr(at_buffer, "+SOCKSTATUS:  1,1") != 0) {
    continueLoop = false;
  }
  
  if (strstr(at_buffer, "+STCPD: 1") != 0) {
    Serial.println(F("Data retrieved"));
  }
  
  if (strstr(at_buffer, "+STCPC: 1") != 0) {
    Serial.println(F("Connection finished by the remote host"));
  }
  
}

static void error(const int errorCode) {    // Error messages 
  int i = 0;
  switch(errorCode) {
    case ERROR_SIM_UNAVAIL:
      Serial.println(F("ERROR: SIM Unavailable"));
      break;
    case ERROR_GPRS_FAIL:
      Serial.println(F("ERROR: Connection to network failed"));
      break;
    case ERROR_NETWORK_FAIL:
      Serial.println(F("ERROR: Could not connect to network"));
      break;
    case ERROR_HOST:
      Serial.println(F("ERROR: Could not connect to host"));
      break;
    case ERROR_GPRS_UNKNOWN:
      Serial.println(F("ERROR: Unknown"));
      break;
    case ERROR_GSM_FAIL:
      Serial.println(F("ERROR: GSM Timeout"));
      break;  
  } 
  Serial.println("ERROR: we'll gonna try again");      
}

void showResults(){          // Show the global variables' values 
  Serial.print(F("Fecha: "));
  Serial.print(min10_hour);
  Serial.print(F(":"));
  Serial.print(min10_minute);
  Serial.print(F(":"));
  Serial.print(min10_sec);
  Serial.print(F(", "));  
  Serial.print(min10_day);
  Serial.print(F("/"));
  Serial.print(min10_month);
  Serial.print(F("/"));
  Serial.println(min10_year);
  Serial.println(F("---- Temperature (Celsius Degrees)----"));
  Serial.print(F("Average Temperature: "));
  Serial.println(tavg);
  Serial.print(F("Max. temperature in this 10 min: "));
  Serial.println(tmax);
  Serial.print(F("Min. temperature in this 10 min: "));
  Serial.println(tmin);
  Serial.print(F("Temperature Deviation: "));
  Serial.println(tstd);  
  Serial.println(F("---- Anemometer (km/h)----"));
  Serial.print(F("Average speed: "));
  Serial.println(vel_avg); 
  Serial.print(F("Maximun speed: "));
  Serial.println(vel_max);   
  Serial.print(F("Minimun speed: "));
  Serial.println(vel_min);
  Serial.print(F("Desviacion velo: "));
  Serial.println(vel_std);
  Serial.println(F("---- Vane ----"));
  Serial.print(F("Average Wind Direction (grades) : "));
  Serial.println(direction_grades);
  Serial.print(F("Modulus wind direction vector  (km/h): "));
  Serial.println(modulus);
  Serial.print(F("Wind U component deviation: "));
  Serial.println(ustd);
  Serial.print(F("Wind V component deviation: "));
  Serial.println(vstd);
  Serial.println(F("---- Pluviometer (l/m2) ----"));
  Serial.print(F("Average Rain fallen in this period: "));
  Serial.println(ravg);
  Serial.print(F("Rain Maximun: "));
  Serial.println(rmax);
  Serial.print(F("Rain Minimum: "));
  Serial.println(rmin);
  Serial.print(F("Rain Standard Deviation: "));
  Serial.println(rstd);
  Serial.print(F("**Rain accumulated (l/m2) until last station restart: "));
  Serial.println(rain_ttal_m2);  
  Serial.println(F("---- Irradiance (range 0-1023) ----"));
  Serial.print(F("Average Luminosity: "));
  Serial.println(lavg);
  Serial.print(F("Maximun Luminosity: "));
  Serial.println(lmax);
  Serial.print(F("Minimun Luminosity: "));
  Serial.println(lmin);
  Serial.print(F("Luminosity standard deviation : "));
  Serial.println(lstd);
}
