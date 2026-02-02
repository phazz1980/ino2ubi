/*Программа для управления камерой*/
#include <SoftwareSerial.h>
#define qwe 12
int sensorPan = A0;     // канал вправо/влево 
int sensorTilt = A1;    // канал вверх/вниз 
int sensorFocus = A2;   // канал фокус
int xVal = 0;           // переменная для хранения значения с потенциометра вправо/влево
int yVal = 0;           // переменная для хранения значения с потенциометра вниз/вверх
int focus = 0;          // переменная для хранения значения с потенциометра фокуса камеры
const byte tiltDown = 0x10;
const byte tiltUp = 0x08;
const byte panRight = 0x02;
const byte panLeft = 0x04;
const byte focusNull = 0x00;  // Зума нет
const byte focusNear = 0x20;  // Зум +  0x01
const byte focusFar = 0x40;   // Зум -  0x80
SoftwareSerial newSerial = SoftwareSerial(7, 8);
void setup()
{
   pinMode(7, INPUT);
   pinMode(8, OUTPUT);
   newSerial.begin(2400); // включаем uart 
}
// отправка данных камере
// структура посылки Pelco-D
/*
|  byte 1  |   byte 2   |  byte 3  |  byte 4  | byte 5 | byte 6 | byte 7 |
 ---------- ------------ ---------- ---------- -------- -------- --------
|Sync 0xFF | Cam Adress | Command1 | Command2 | Data 1 | Data 2 |Checksum|
*/
void sendData(byte camNum, byte command_1, byte command_2, byte panSpeed, byte tiltSpeed) 
{
   int modSum = 0;                 // начальное нулевое значение контрольной суммы 
   byte dataVal[6] = {0xFF, camNum, command_1, command_2, panSpeed, tiltSpeed}; // вектор формата комманды Pelco-D
   for (int i=0; i<6; i++)         // цикл отправки посылки камере
   {
      newSerial.write(dataVal[i]);  // отправить байт в UART
      if (i > 0)                   // контрольная сумма начинает считаться со второго байта, поэтому первый 0xFF пропускаем
         modSum += dataVal[i];     // суммируем байты контрольной суммы
   }
   modSum %= 100;                  // контрольная сумма делиться по модуля на 256 в dec или по другому на 100 в hex
   newSerial.write(modSum);         // отправить контрольную сумму
}
void halt()
{
   byte dataVal[7] = {0xFF, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01};
   for (int i=0; i<7; i++)
   {
      newSerial.write(dataVal[i]);  // отправить байт в UART   
   } 
}
void loop() 
{
   xVal = analogRead(sensorPan);     // считывание значения потенциометра вправо/влево в соответствующую переменную
   yVal = analogRead(sensorTilt);    // считывание значения потенциометра вниз/вверх в соответствующую переменную
   focus = analogRead(sensorFocus);  // считывание значения потенциометра фокуса камеры в соответствующую переменную
   
   if (xVal > 600)  
   { 
      sendData(0x01, focusNull, panRight, 0x3F, 0x00);      // вызывается функция отправки байта
      while (xVal > 600) 
      {
         xVal = analogRead(sensorPan);   
      }
   }
   if (xVal < 450)
   {
      sendData(0x01, focusNull, panLeft, 0x3F, 0x00);      // вызывается функция отправки байта  
      while (xVal < 450) 
      {
         xVal = analogRead(sensorPan);   
      }
   }
 
   if (yVal > 600)
   {
      sendData(0x01, focusNull, tiltUp, 0x00, 0x3F);      // вызывается функция отправки байта
      while (yVal > 600) 
      {
         yVal = analogRead(sensorTilt);   
      }
   } 
   if (yVal < 450)
   {
      sendData(0x01, focusNull, tiltDown, 0x00, 0x3F);      // вызывается функция отправки байта  
      while (yVal < 450) 
      {
         yVal = analogRead(sensorTilt);   
      }
   }  
   
   if (focus > 600)
   {
      sendData(0x01, focusNull, focusNear, 0x00, 0x00);      // вызывается функция отправки байта
      while (focus > 600) 
      {
         focus = analogRead(sensorFocus);   
      }
   } 
   if (focus < 450)
   {
      sendData(0x01, focusNull, focusFar, 0x00, 0x00);      // вызывается функция отправки байта  
      while (focus < 450) 
      {
         focus = analogRead(sensorFocus);   
      }
   } 
   halt();
}
